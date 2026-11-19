"""
BankFlow AI - Duplicate Message Protection Tests
Tests idempotency layer, duplicate detection, handler replay prevention, and delivery attempt logging.
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
from app.messaging.duplicate_protection import DuplicateProtectionService
from app.messaging.consumer import MessageConsumer
import json


def test_duplicate_message_detected_and_skipped(db_session: Session):
    """Verify that a message with an already registered message_id is flagged as duplicate."""
    msg = StandardBankingMessage(
        request_id="REQ-DUP-01",
        sender_agent_id="AGT-INTAKE-01",
        receiver_agent_id="RequestAgentPool",
        event_type=BankingEventType.REQUEST_CLASSIFIED,
    )

    # 1. First reception: not duplicate
    is_dup1, rec1 = DuplicateProtectionService.record_received_message(
        db=db_session,
        message=msg,
        consumer_name="RequestAgent_1",
    )
    assert is_dup1 is False
    assert rec1 is not None
    assert rec1.processing_status == "PROCESSING"

    DuplicateProtectionService.mark_message_completed(
        db=db_session,
        message_id=msg.message_id,
        consumer_name="RequestAgent_1",
    )

    # 2. Second reception of same message: must be detected as duplicate
    is_dup2, rec2 = DuplicateProtectionService.record_received_message(
        db=db_session,
        message=msg,
        consumer_name="RequestAgent_1",
    )
    assert is_dup2 is True

    # 3. Verify duplicate delivery attempt logged
    attempt = (
        db_session.query(MessageDeliveryAttempt)
        .filter(
            MessageDeliveryAttempt.message_id == msg.message_id,
            MessageDeliveryAttempt.delivery_status == "DUPLICATE_IGNORED",
        )
        .first()
    )
    assert attempt is not None


def test_consumer_idempotency_prevents_duplicate_handler_execution(db_session: Session):
    """Verify MessageConsumer runs handler on initial receipt but skips on duplicate."""
    msg = StandardBankingMessage(
        request_id="REQ-IDEMP-01",
        sender_agent_id="AGT-VERIF-01",
        receiver_agent_id="ServiceAgent_CHEQUE_BOOK",
        event_type=BankingEventType.VERIFICATION_COMPLETED,
    )
    body_bytes = json.dumps(msg.to_json_dict()).encode("utf-8")

    execution_count = 0

    def counting_handler(db, m):
        nonlocal execution_count
        execution_count += 1

    # First execution
    res1 = MessageConsumer.process_raw_message(
        db=db_session,
        body_bytes=body_bytes,
        consumer_name="ServiceAgent_CHEQUE_BOOK",
        handler=counting_handler,
    )
    assert res1["status"] == "PROCESSED"
    assert execution_count == 1

    # Second execution of identical message payload
    res2 = MessageConsumer.process_raw_message(
        db=db_session,
        body_bytes=body_bytes,
        consumer_name="ServiceAgent_CHEQUE_BOOK",
        handler=counting_handler,
    )
    assert res2["status"] == "DUPLICATE_SKIPPED"
    # Handler must NOT have been executed a second time!
    assert execution_count == 1
