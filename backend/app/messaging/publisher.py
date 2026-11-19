"""
BankFlow AI - Message Publisher
Handles publishing of validated messages to RabbitMQ with publisher confirms and outbox database persistence.
"""

import json
import logging
import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import pika
from sqlalchemy.orm import Session

from app.config import settings
from app.messaging.connection import connection_manager
from app.messaging.circuit_breaker import rabbitmq_circuit_breaker, CircuitBreakerOpenException
from app.messaging.message_schema import StandardBankingMessage, BankingEventType
from app.messaging.routing import MAIN_EXCHANGE, get_routing_key
from app.messaging.exchanges import declare_exchanges
from app.models.agent_event import AgentEvent

logger = logging.getLogger("bankflow_ai.messaging.publisher")


class MessagePublisher:
    """
    Centralized event publisher.
    Enforces outbox persistence in PostgreSQL before message emission.
    """

    @staticmethod
    def publish_event(
        db: Session,
        message: StandardBankingMessage,
        previous_state: Optional[str] = None,
        new_state: Optional[str] = None,
        exchange: str = MAIN_EXCHANGE,
        routing_key: Optional[str] = None,
    ) -> StandardBankingMessage:
        """
        Publishes a standard banking event to RabbitMQ.
        Simultaneously records an immutable AgentEvent in PostgreSQL for full communication history.
        """
        # 1. Determine routing key
        actual_routing_key = routing_key or get_routing_key(message.event_type)

        # 2. Record AgentEvent in PostgreSQL (Transactional Outbox)
        event_record = AgentEvent(
            event_id=f"EVT-{uuid.uuid4().hex[:12].upper()}",
            request_id=message.request_id,
            agent_id=message.sender_agent_id,
            event_type=message.event_type.value if hasattr(message.event_type, "value") else str(message.event_type),
            previous_state=previous_state,
            new_state=new_state,
            timestamp=message.timestamp,
            reason_code=message.reason_code,
            payload=message.payload,
        )
        db.add(event_record)
        db.flush()

        # 3. Publish to RabbitMQ with Publisher Confirms and Circuit Breaker protection
        if not rabbitmq_circuit_breaker.can_execute():
            logger.warning(
                "RabbitMQ Circuit Breaker is OPEN. Outbox event '%s' persisted in DB, broker publish skipped.",
                event_record.event_id,
            )
            raise CircuitBreakerOpenException(
                f"RabbitMQ Circuit Breaker '{rabbitmq_circuit_breaker.name}' is OPEN. Publish rejected."
            )

        try:
            ch = connection_manager.get_sync_channel()
            # Ensure exchanges exist
            declare_exchanges(ch)

            body_json = json.dumps(message.to_json_dict())
            properties = pika.BasicProperties(
                content_type="application/json",
                content_encoding="utf-8",
                delivery_mode=2,  # Persistent message
                message_id=message.message_id,
                correlation_id=message.correlation_id,
                timestamp=int(message.timestamp.timestamp()),
                headers={
                    "event_type": message.event_type.value if hasattr(message.event_type, "value") else str(message.event_type),
                    "sender_agent_id": message.sender_agent_id,
                    "receiver_agent_id": message.receiver_agent_id,
                    "request_version": message.request_version,
                    "retry_count": message.retry_count,
                },
            )

            ch.basic_publish(
                exchange=exchange,
                routing_key=actual_routing_key,
                body=body_json.encode("utf-8"),
                properties=properties,
                mandatory=False,
            )
            rabbitmq_circuit_breaker.record_success()
            logger.info(
                "Published message '%s' [%s] to '%s' (routing: '%s')",
                message.message_id,
                message.event_type,
                exchange,
                actual_routing_key,
            )
            return message
        except Exception as e:
            rabbitmq_circuit_breaker.record_failure(e)
            logger.error("Failed to publish message '%s' to RabbitMQ: %s", message.message_id, str(e))
            raise

    @staticmethod
    async def publish_event_async(
        db: Session,
        message: StandardBankingMessage,
        previous_state: Optional[str] = None,
        new_state: Optional[str] = None,
        exchange_name: str = MAIN_EXCHANGE,
        routing_key: Optional[str] = None,
    ) -> StandardBankingMessage:
        """Asynchronous variant of publish_event using aio-pika."""
        import aio_pika

        actual_routing_key = routing_key or get_routing_key(message.event_type)

        # 1. Record Outbox Event
        event_record = AgentEvent(
            event_id=f"EVT-{uuid.uuid4().hex[:12].upper()}",
            request_id=message.request_id,
            agent_id=message.sender_agent_id,
            event_type=message.event_type.value if hasattr(message.event_type, "value") else str(message.event_type),
            previous_state=previous_state,
            new_state=new_state,
            timestamp=message.timestamp,
            reason_code=message.reason_code,
            payload=message.payload,
        )
        db.add(event_record)
        db.flush()

        # 2. Publish async
        channel = await connection_manager.get_async_channel()
        exchange = await channel.get_exchange(exchange_name)

        body_json = json.dumps(message.to_json_dict())
        amqp_msg = aio_pika.Message(
            body=body_json.encode("utf-8"),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            message_id=message.message_id,
            correlation_id=message.correlation_id,
            content_type="application/json",
            headers={
                "event_type": message.event_type.value if hasattr(message.event_type, "value") else str(message.event_type),
                "sender_agent_id": message.sender_agent_id,
                "receiver_agent_id": message.receiver_agent_id,
                "request_version": message.request_version,
                "retry_count": message.retry_count,
            },
        )

        await exchange.publish(amqp_msg, routing_key=actual_routing_key)
        return message
