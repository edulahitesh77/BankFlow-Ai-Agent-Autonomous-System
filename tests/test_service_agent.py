"""
BankFlow AI - Service Agent Pool Tests
Tests skill compatibility, service execution, and simulated fulfillment metadata.
"""

import sys
import os
import pytest
from sqlalchemy.orm import Session

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.models.request import Request, ServiceType, RequestStatus
from app.simulation.model import BankingSimulationModel


def test_service_agent_skill_compatibility():
    """Verify ServiceAgent accepts only requests matching its configured skills."""
    model = BankingSimulationModel()
    cheque_svc = model.get_service_agents()[0]  # ServiceAgent_CHEQUE_BOOK

    assert cheque_svc.can_handle_service(ServiceType.CHEQUE_BOOK) is True
    assert cheque_svc.can_handle_service(ServiceType.DEBIT_CARD_REPLACEMENT) is False


def test_service_agent_rejects_unverified_requests(db_session: Session, sample_customer_and_account):
    """Verify ServiceAgent raises ValueError if a request is not in VERIFIED status."""
    customer, account = sample_customer_and_account
    model = BankingSimulationModel()
    cheque_svc = model.get_service_agents()[0]

    req = Request(
        request_id="REQ-SVC-UNVERIF",
        customer_id=customer.id,
        account_id=account.id,
        service_type=ServiceType.CHEQUE_BOOK,
        request_status=RequestStatus.QUEUED,  # Not VERIFIED
    )
    db_session.add(req)
    db_session.flush()

    with pytest.raises(ValueError):
        cheque_svc.execute_service(db_session, req)


def test_service_agent_executes_fulfillment_successfully(db_session: Session, sample_customer_and_account):
    """Verify ServiceAgent completes verified requests and records simulated dispatch data."""
    customer, account = sample_customer_and_account
    model = BankingSimulationModel()
    cheque_svc = model.get_service_agents()[0]

    req = Request(
        request_id="REQ-SVC-DONE",
        customer_id=customer.id,
        account_id=account.id,
        service_type=ServiceType.CHEQUE_BOOK,
        request_status=RequestStatus.VERIFIED,
        payload={"number_of_leaves": 50},
    )
    db_session.add(req)
    db_session.flush()

    completed_req = cheque_svc.execute_service(db_session, req)
    assert completed_req.request_status == RequestStatus.COMPLETED
    assert completed_req.completed_at is not None
    assert "fulfillment_data" in completed_req.payload
    assert completed_req.payload["fulfillment_data"]["leaves_dispatched"] == 50
    assert cheque_svc.is_available is True
    assert cheque_svc.completed_work_count == 1
