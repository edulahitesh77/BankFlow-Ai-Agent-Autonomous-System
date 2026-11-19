"""
BankFlow AI - Duplicate Message Protection
Implements database-backed idempotent message processing using PostgreSQL ProcessedMessages registry.
"""

import logging
from typing import Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.processed_message import ProcessedMessage
from app.models.delivery_attempt import MessageDeliveryAttempt
from app.messaging.message_schema import StandardBankingMessage

logger = logging.getLogger("bankflow_ai.messaging.duplicate_protection")


class DuplicateMessageError(Exception):
    """Raised when a duplicate message is detected that was already processed."""
    pass


class DuplicateProtectionService:
    """
    Guarantees idempotency across all agent consumers.
    Ensures that identical message IDs are never processed multiple times.
    """

    @staticmethod
    def is_message_already_processed(db: Session, message_id: str) -> bool:
        """Checks if a message ID has already been recorded as processed."""
        record = db.query(ProcessedMessage).filter(ProcessedMessage.message_id == message_id).first()
        return record is not None and record.processing_status in ["PROCESSED", "COMPLETED"]

    @staticmethod
    def record_received_message(
        db: Session,
        message: StandardBankingMessage,
        consumer_name: str,
    ) -> Tuple[bool, Optional[ProcessedMessage]]:
        """
        Attempts to register an incoming message in ProcessedMessages.
        Returns:
            (is_duplicate: bool, record: Optional[ProcessedMessage])
        """
        existing = db.query(ProcessedMessage).filter(ProcessedMessage.message_id == message.message_id).first()
        if existing:
            logger.warning(
                "Duplicate message detected! Message ID '%s' (Event: %s) already received by consumer '%s'.",
                message.message_id,
                message.event_type,
                consumer_name,
            )
            # Log duplicate attempt
            attempt = MessageDeliveryAttempt(
                message_id=message.message_id,
                consumer_name=consumer_name,
                attempt_number=existing.retry_count + 1,
                delivery_status="DUPLICATE_IGNORED",
                error_message="Duplicate message skipped by idempotency guard.",
            )
            db.add(attempt)
            db.commit()
            return True, existing

        try:
            # Create fresh processing record
            new_record = ProcessedMessage(
                message_id=message.message_id,
                request_id=message.request_id,
                event_type=message.event_type.value if hasattr(message.event_type, "value") else str(message.event_type),
                consumer_name=consumer_name,
                processing_status="PROCESSING",
                retry_count=message.retry_count,
                payload_snapshot=message.payload,
            )
            db.add(new_record)
            db.flush()
            return False, new_record
        except IntegrityError:
            db.rollback()
            logger.warning("Concurrent duplicate message registration collision for '%s'.", message.message_id)
            existing = db.query(ProcessedMessage).filter(ProcessedMessage.message_id == message.message_id).first()
            return True, existing

    @staticmethod
    def mark_message_completed(
        db: Session,
        message_id: str,
        consumer_name: str,
    ) -> None:
        """Marks a registered message as successfully processed."""
        record = db.query(ProcessedMessage).filter(ProcessedMessage.message_id == message_id).first()
        if record:
            record.processing_status = "PROCESSED"
            record.processed_at = datetime.now(timezone.utc)
            db.flush()

        # Record successful delivery attempt
        attempt = MessageDeliveryAttempt(
            message_id=message_id,
            consumer_name=consumer_name,
            attempt_number=(record.retry_count if record else 0) + 1,
            delivery_status="SUCCESS",
        )
        db.add(attempt)
        db.commit()

    @staticmethod
    def mark_message_failed(
        db: Session,
        message_id: str,
        consumer_name: str,
        error_message: str,
        is_dead_letter: bool = False,
        request_id: Optional[str] = None,
        event_type: Optional[str] = None,
        payload: Optional[dict] = None,
    ) -> ProcessedMessage:
        """Marks a registered message as failed or dead-lettered, creating record if absent."""
        record = db.query(ProcessedMessage).filter(ProcessedMessage.message_id == message_id).first()
        if record:
            record.processing_status = "DEAD_LETTER" if is_dead_letter else "FAILED"
            record.error_message = error_message
            record.retry_count += 1
            db.flush()
        else:
            record = ProcessedMessage(
                message_id=message_id,
                request_id=request_id or "UNKNOWN",
                event_type=event_type or "FAILED_EVENT",
                consumer_name=consumer_name,
                processing_status="DEAD_LETTER" if is_dead_letter else "FAILED",
                retry_count=1,
                error_message=error_message,
                payload_snapshot=payload,
            )
            db.add(record)
            db.flush()

        # Record attempt
        attempt = MessageDeliveryAttempt(
            message_id=message_id,
            consumer_name=consumer_name,
            attempt_number=(record.retry_count if record else 1),
            delivery_status="DEAD_LETTER" if is_dead_letter else "RETRY",
            error_message=error_message,
        )
        db.add(attempt)
        db.commit()
        return record
