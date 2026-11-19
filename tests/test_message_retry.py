"""
BankFlow AI - Message Retry & Dead Letter Tests
Tests retry policy, backoff attempts tracking, dead-letter routing on limit exhaustion,
and authorized message recovery.
"""

import sys
import os
import pytest
from sqlalchemy.orm import Session

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.models.processed_message import ProcessedMessage
from app.models.delivery_attempt import MessageDeliveryAttempt
from app.messaging.message_schema import StandardBankingMessage, BankingEventType
from app.messaging.retry import RetryPolicyService
from app.messaging.dead_letter import DeadLetterService
from app.messaging.queues import declare_queues_and_bindings


def test_transient_failure_increments_retry_count(db_session: Session):
    """Verify transient error triggers retry and logs attempt with status RETRY."""
    declare_queues_and_bindings()

    msg = StandardBankingMessage(
        request_id="REQ-RETRY-01",
        sender_agent_id="AGT-INTAKE-01",
        receiver_agent_id="RequestAgentPool",
        event_type=BankingEventType.REQUEST_CLASSIFIED,
        retry_count=0,
    )

    retried = RetryPolicyService.handle_failure(
        db=db_session,
        message=msg,
        consumer_name="RequestAgent_1",
        error_message="Database transient lock timeout",
    )

    assert retried is True
    assert msg.retry_count == 1

    rec = db_session.query(ProcessedMessage).filter(ProcessedMessage.message_id == msg.message_id).first()
    assert rec is not None
    assert rec.processing_status == "FAILED"
    assert rec.retry_count == 1

    attempt = (
        db_session.query(MessageDeliveryAttempt)
        .filter(MessageDeliveryAttempt.message_id == msg.message_id)
        .order_by(MessageDeliveryAttempt.attempt_number.desc())
        .first()
    )
    assert attempt.delivery_status == "RETRY"


def test_max_retries_exceeded_routes_to_dead_letter(db_session: Session):
    """Verify exceeding MAX_RETRIES routes message to DEAD_LETTER."""
    declare_queues_and_bindings()

    msg = StandardBankingMessage(
        request_id="REQ-DEAD-01",
        sender_agent_id="AGT-VERIF-01",
        receiver_agent_id="ServiceAgent_CHEQUE_BOOK",
        event_type=BankingEventType.VERIFICATION_COMPLETED,
        retry_count=3,  # Already at max retries (3)
    )

    retried = RetryPolicyService.handle_failure(
        db=db_session,
        message=msg,
        consumer_name="ServiceAgent_CHEQUE_BOOK",
        error_message="Permanent ledger communication error",
    )

    # Must NOT retry again
    assert retried is False

    rec = db_session.query(ProcessedMessage).filter(ProcessedMessage.message_id == msg.message_id).first()
    assert rec is not None
    assert rec.processing_status == "DEAD_LETTER"

    # Verify dead letter listing includes this message
    dead_letters = DeadLetterService.list_dead_letters(db=db_session)
    msg_ids = [m["message_id"] for m in dead_letters["items"]]
    assert msg.message_id in msg_ids


def test_authorized_dead_letter_replay(db_session: Session):
    """Verify authorized staff can replay a dead-letter message with fresh retry budget."""
    declare_queues_and_bindings()

    msg = StandardBankingMessage(
        request_id="REQ-REPLAY-01",
        sender_agent_id="AGT-INTAKE-01",
        receiver_agent_id="RequestAgentPool",
        event_type=BankingEventType.REQUEST_CLASSIFIED,
        retry_count=3,
    )

    # Force to dead letter
    RetryPolicyService.handle_failure(
        db=db_session,
        message=msg,
        consumer_name="RequestAgent_1",
        error_message="Fatal network partition",
    )

    # Authorized officer initiates replay
    replay_res = DeadLetterService.retry_dead_letter_message(
        db=db_session,
        message_id=msg.message_id,
        authorized_officer="officer_alexander",
    )

    assert replay_res["status"] == "RE_QUEUED"
    assert replay_res["retried_by"] == "officer_alexander"

    # Status updated in database
    rec = db_session.query(ProcessedMessage).filter(ProcessedMessage.message_id == msg.message_id).first()
    assert rec.processing_status == "RETRIED"
