"""
BankFlow AI - Message Retry Policy
Controls exponential/controlled message retry logic, maximum retry enforcement,
and routing exhausted failures to the dead-letter exchange.
"""

import logging
from typing import Optional
from sqlalchemy.orm import Session

from app.config import settings
from app.messaging.message_schema import StandardBankingMessage
from app.messaging.routing import MAIN_EXCHANGE, DEAD_LETTER_EXCHANGE, get_routing_key
from app.messaging.duplicate_protection import DuplicateProtectionService

logger = logging.getLogger("bankflow_ai.messaging.retry")


class RetryPolicyService:
    """
    Manages safe message retry logic without infinite loops.
    Routes unrecoverable failures to the dead-letter exchange.
    """

    @staticmethod
    def handle_failure(
        db: Session,
        message: StandardBankingMessage,
        consumer_name: str,
        error_message: str,
    ) -> bool:
        """
        Evaluates failure against retry limits.
        If retry_count < MAX_RETRIES: re-publishes with incremented counter.
        If limit reached: marks message as DEAD_LETTER.
        Returns:
            True if retried, False if routed to Dead Letter.
        """
        from app.messaging.publisher import MessagePublisher

        next_retry_count = message.retry_count + 1

        event_type_str = message.event_type.value if hasattr(message.event_type, "value") else str(message.event_type)

        if next_retry_count <= settings.RABBITMQ_MAX_RETRIES:
            logger.warning(
                "Retrying message '%s' (Attempt %s/%s) on consumer '%s': %s",
                message.message_id,
                next_retry_count,
                settings.RABBITMQ_MAX_RETRIES,
                consumer_name,
                error_message,
            )
            # Update retry count in message
            message.retry_count = next_retry_count
            DuplicateProtectionService.mark_message_failed(
                db=db,
                message_id=message.message_id,
                consumer_name=consumer_name,
                error_message=error_message,
                is_dead_letter=False,
                request_id=message.request_id,
                event_type=event_type_str,
                payload=message.payload,
            )

            # Re-publish to main exchange with incremented retry count
            MessagePublisher.publish_event(
                db=db,
                message=message,
                exchange=MAIN_EXCHANGE,
                routing_key=get_routing_key(message.event_type),
            )
            return True
        else:
            logger.error(
                "Max retries (%s) exceeded for message '%s'. Routing to DEAD_LETTER_EXCHANGE. Error: %s",
                settings.RABBITMQ_MAX_RETRIES,
                message.message_id,
                error_message,
            )
            DuplicateProtectionService.mark_message_failed(
                db=db,
                message_id=message.message_id,
                consumer_name=consumer_name,
                error_message=f"Exceeded max retries ({settings.RABBITMQ_MAX_RETRIES}): {error_message}",
                is_dead_letter=True,
                request_id=message.request_id,
                event_type=event_type_str,
                payload=message.payload,
            )

            # Re-publish directly to Dead Letter Exchange
            MessagePublisher.publish_event(
                db=db,
                message=message,
                exchange=DEAD_LETTER_EXCHANGE,
                routing_key="deadletter.exhausted",
            )
            return False
