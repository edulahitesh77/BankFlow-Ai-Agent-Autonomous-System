"""
BankFlow AI - Dead Letter Management
Provides inspection and safe replay of dead-lettered messages for authorized staff.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.processed_message import ProcessedMessage
from app.models.delivery_attempt import MessageDeliveryAttempt
from app.messaging.message_schema import StandardBankingMessage, BankingEventType
from app.messaging.publisher import MessagePublisher
from app.messaging.routing import MAIN_EXCHANGE, get_routing_key

logger = logging.getLogger("bankflow_ai.messaging.dead_letter")


class DeadLetterService:
    """Service allowing authorized bank operations officers to inspect and retry dead-letter messages."""

    @staticmethod
    def list_dead_letters(
        db: Session,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """Lists messages that have failed and transitioned to DEAD_LETTER status."""
        query = db.query(ProcessedMessage).filter(ProcessedMessage.processing_status == "DEAD_LETTER")
        total = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(ProcessedMessage.received_at.desc()).offset(offset).limit(page_size).all()

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [
                {
                    "id": m.id,
                    "message_id": m.message_id,
                    "request_id": m.request_id,
                    "event_type": m.event_type,
                    "consumer_name": m.consumer_name,
                    "processing_status": m.processing_status,
                    "retry_count": m.retry_count,
                    "received_at": m.received_at.isoformat() if m.received_at else None,
                    "processed_at": m.processed_at.isoformat() if m.processed_at else None,
                    "error_message": m.error_message,
                    "payload_snapshot": m.payload_snapshot,
                }
                for m in items
            ],
        }

    @staticmethod
    def retry_dead_letter_message(
        db: Session,
        message_id: str,
        authorized_officer: str,
    ) -> Dict[str, Any]:
        """
        Safely recovers a dead-letter message and re-queues it into the main exchange
        with a fresh retry budget and supervisory audit trail.
        """
        record = db.query(ProcessedMessage).filter(ProcessedMessage.message_id == message_id).first()
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dead letter message with ID '{message_id}' not found.",
            )

        # Reconstruct standard message
        event_type_val = record.event_type
        try:
            event_type_enum = BankingEventType(event_type_val)
        except ValueError:
            event_type_enum = BankingEventType.REQUEST_CREATED

        reconstructed_msg = StandardBankingMessage(
            message_id=record.message_id,
            request_id=record.request_id or "UNKNOWN",
            request_version=0,
            sender_agent_id=f"RETRY_SUPERVISOR_{authorized_officer}",
            receiver_agent_id=record.consumer_name,
            event_type=event_type_enum,
            timestamp=datetime.now(timezone.utc),
            payload=record.payload_snapshot or {},
            reason_code=f"MANUAL_STAFF_RETRY_BY_{authorized_officer}",
            retry_count=0,  # Reset retry budget
        )

        # Update status in DB
        record.processing_status = "RETRIED"
        record.error_message = f"Manually retried by officer '{authorized_officer}' at {datetime.now(timezone.utc).isoformat()}."
        db.flush()

        # Record manual attempt
        attempt = MessageDeliveryAttempt(
            message_id=message_id,
            consumer_name=record.consumer_name,
            attempt_number=record.retry_count + 1,
            delivery_status="RETRY",
            error_message=f"Manual retry initiated by officer '{authorized_officer}'.",
        )
        db.add(attempt)
        db.commit()

        # Re-publish to main exchange
        MessagePublisher.publish_event(
            db=db,
            message=reconstructed_msg,
            exchange=MAIN_EXCHANGE,
            routing_key=get_routing_key(event_type_enum),
        )

        logger.info(
            "Officer '%s' successfully re-queued dead-letter message '%s' into '%s'.",
            authorized_officer,
            message_id,
            MAIN_EXCHANGE,
        )

        return {
            "message_id": message_id,
            "status": "RE_QUEUED",
            "retried_by": authorized_officer,
            "routing_key": get_routing_key(event_type_enum),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
