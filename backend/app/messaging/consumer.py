"""
BankFlow AI - Message Consumer
Handles manual acknowledgement, message parsing, schema validation,
idempotency checking, version validation, and dispatch to agent processors.
"""

import json
import logging
from typing import Callable, Optional, Dict, Any, List
import pika
from pika.adapters.blocking_connection import BlockingChannel
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.request import Request
from app.messaging.connection import connection_manager
from app.messaging.message_schema import StandardBankingMessage, BankingEventType
from app.messaging.duplicate_protection import DuplicateProtectionService
from app.messaging.retry import RetryPolicyService

logger = logging.getLogger("bankflow_ai.messaging.consumer")


class MessageConsumer:
    """
    Consumer processing messages with manual acknowledgement.
    Guarantees that messages are acknowledged only after successful persistence.
    """

    @staticmethod
    def process_raw_message(
        db: Session,
        body_bytes: bytes,
        consumer_name: str,
        handler: Callable[[Session, StandardBankingMessage], Any],
    ) -> Dict[str, Any]:
        """
        Parses, validates, deduplicates, and dispatches a single raw AMQP message body.
        """
        # 1. Parse JSON
        try:
            body_dict = json.loads(body_bytes.decode("utf-8"))
        except Exception as e:
            logger.error("Consumer '%s' rejected malformed non-JSON message: %s", consumer_name, str(e))
            return {"status": "REJECTED_MALFORMED", "error": f"Invalid JSON: {str(e)}"}

        # 2. Validate Standard Message Schema
        try:
            message = StandardBankingMessage(**body_dict)
        except Exception as e:
            logger.error("Consumer '%s' rejected message schema violation: %s", consumer_name, str(e))
            return {"status": "REJECTED_SCHEMA_VIOLATION", "error": f"Schema violation: {str(e)}"}

        # 3. Duplicate Protection (Idempotency)
        is_dup, processed_record = DuplicateProtectionService.record_received_message(
            db=db,
            message=message,
            consumer_name=consumer_name,
        )
        if is_dup:
            logger.info("Message '%s' is duplicate. Skipping execution.", message.message_id)
            return {"status": "DUPLICATE_SKIPPED", "message_id": message.message_id}

        # 4. Request Version & Ownership Consistency Check
        if message.request_id and message.request_id != "UNKNOWN":
            db_req = db.query(Request).filter(Request.request_id == message.request_id).first()
            if db_req:
                # If message version is strictly older than DB version, it is stale
                if message.request_version < db_req.assignment_version:
                    logger.warning(
                        "Consumer '%s' rejected stale message '%s' (Msg Ver: %s < DB Ver: %s).",
                        consumer_name,
                        message.message_id,
                        message.request_version,
                        db_req.assignment_version,
                    )
                    DuplicateProtectionService.mark_message_failed(
                        db=db,
                        message_id=message.message_id,
                        consumer_name=consumer_name,
                        error_message=f"Stale message version: msg={message.request_version}, db={db_req.assignment_version}",
                        is_dead_letter=True,
                    )
                    return {"status": "STALE_VERSION_REJECTED", "message_id": message.message_id}

        # 5. Execute Agent Handler
        try:
            handler(db, message)
            DuplicateProtectionService.mark_message_completed(
                db=db,
                message_id=message.message_id,
                consumer_name=consumer_name,
            )
            return {"status": "PROCESSED", "message_id": message.message_id}
        except Exception as e:
            logger.error("Handler error processing message '%s' on '%s': %s", message.message_id, consumer_name, str(e))
            retried = RetryPolicyService.handle_failure(
                db=db,
                message=message,
                consumer_name=consumer_name,
                error_message=str(e),
            )
            return {
                "status": "RETRIED" if retried else "DEAD_LETTER",
                "message_id": message.message_id,
                "error": str(e),
            }

    @staticmethod
    def consume_batch(
        queue_name: str,
        consumer_name: str,
        handler: Callable[[Session, StandardBankingMessage], Any],
        max_messages: int = 10,
        channel: Optional[BlockingChannel] = None,
    ) -> List[Dict[str, Any]]:
        """
        Polls up to max_messages from a queue, processes each with manual ack,
        and safely closes or returns channel.
        """
        ch = channel or connection_manager.get_sync_channel()
        results = []

        for _ in range(max_messages):
            method_frame, header_frame, body = ch.basic_get(queue=queue_name, auto_ack=False)
            if method_frame is None:
                # Queue is currently empty
                break

            delivery_tag = method_frame.delivery_tag
            db: Session = SessionLocal()
            try:
                res = MessageConsumer.process_raw_message(
                    db=db,
                    body_bytes=body,
                    consumer_name=consumer_name,
                    handler=handler,
                )
                results.append(res)
                # Manually acknowledge the message only after processing & persistence
                ch.basic_ack(delivery_tag=delivery_tag)
            except Exception as e:
                logger.error("Fatal consumer error on '%s': %s. Nacking message.", queue_name, str(e))
                # Requeue = False routes to dead-letter exchange if DLX is configured
                ch.basic_nack(delivery_tag=delivery_tag, requeue=False)
            finally:
                db.close()

        return results
