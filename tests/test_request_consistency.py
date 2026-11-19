"""
BankFlow AI - Request Consistency & Ownership Tests
Tests transactional request ownership checks, version validation, stale event rejection,
and duplicate completion protection.
"""

import sys
import os
import pytest
from sqlalchemy.orm import Session
import json

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.models.request import Request, ServiceType, RequestStatus
from app.simulation.model import BankingSimulationModel
from app.simulation.state_machine import DuplicateCompletionError, transition_request
from app.messaging.message_schema import StandardBankingMessage, BankingEventType
from app.messaging.consumer import MessageConsumer


def test_request_agent_single_ownership_enforcement(db_session: Session, sample_customer_and_account):
    """Verify each RequestAgent can own at most one active request version at a time."""
    customer, account = sample_customer_and_account
    model = BankingSimulationModel()
    agent = model.get_request_agents()[0]

    req1 = Request(
        request_id="REQ-OWN-CONSIST-1",
        customer_id=customer.id,
        account_id=account.id,
        service_type=ServiceType.CHEQUE_BOOK,
        request_status=RequestStatus.CLASSIFIED,
        assignment_version=0,
    )
    req2 = Request(
        request_id="REQ-OWN-CONSIST-2",
        customer_id=customer.id,
        account_id=account.id,
        service_type=ServiceType.CHEQUE_BOOK,
        request_status=RequestStatus.CLASSIFIED,
        assignment_version=0,
    )
    db_session.add_all([req1, req2])
    db_session.flush()

    # Worker accepts req1
    agent.accept_and_queue_request(db_session, req1)
    assert agent.is_available is False
    assert agent.current_request_id == "REQ-OWN-CONSIST-1"

    # Attempting to assign req2 to same worker must fail with RuntimeError
    with pytest.raises(RuntimeError):
        agent.accept_and_queue_request(db_session, req2)


def test_stale_message_version_rejected_by_consumer(db_session: Session, sample_customer_and_account):
    """Verify that consumer rejects stale messages whose version is older than current DB version."""
    customer, account = sample_customer_and_account

    # Request in DB is on version 2 (e.g. after customer correction)
    req = Request(
        request_id="REQ-STALE-01",
        customer_id=customer.id,
        account_id=account.id,
        service_type=ServiceType.CHEQUE_BOOK,
        request_status=RequestStatus.NEW,
        assignment_version=2,
    )
    db_session.add(req)
    db_session.flush()

    # Incoming message carries old version 1
    stale_msg = StandardBankingMessage(
        request_id="REQ-STALE-01",
        request_version=1,  # Stale! (DB is at version 2)
        sender_agent_id="OldWorker_1",
        receiver_agent_id="AGT-VERIF-01",
        event_type=BankingEventType.REQUEST_ACCEPTED,
    )
    body_bytes = json.dumps(stale_msg.to_json_dict()).encode("utf-8")

    res = MessageConsumer.process_raw_message(
        db=db_session,
        body_bytes=body_bytes,
        consumer_name="AGT-VERIF-01",
        handler=lambda d, m: None,
    )

    assert res["status"] == "STALE_VERSION_REJECTED"


def test_duplicate_completion_protection(db_session: Session, sample_customer_and_account):
    """Verify state machine strictly forbids duplicate transitions from COMPLETED status."""
    customer, account = sample_customer_and_account

    req = Request(
        request_id="REQ-DONE-PROTECT",
        customer_id=customer.id,
        account_id=account.id,
        service_type=ServiceType.CHEQUE_BOOK,
        request_status=RequestStatus.COMPLETED,
    )
    db_session.add(req)
    db_session.flush()

    # Attempting to re-execute or transition completed request raises DuplicateCompletionError
    with pytest.raises(DuplicateCompletionError):
        transition_request(
            db=db_session,
            request=req,
            new_status=RequestStatus.IN_SERVICE,
            agent_code="LateWorker",
        )
