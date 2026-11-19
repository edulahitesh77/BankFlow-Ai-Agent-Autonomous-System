"""
BankFlow AI - Request Agent Pool Tests
Tests multiple concurrent worker instances, single request ownership, and release rules.
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


def test_request_agent_pool_creation_and_config():
    """Verify Request Agent pool creates configurable number of worker instances."""
    model = BankingSimulationModel()
    workers = model.get_request_agents()
    assert len(workers) == 3
    assert workers[0].agent_code == "RequestAgent_1"
    assert workers[1].agent_code == "RequestAgent_2"
    assert workers[2].agent_code == "RequestAgent_3"
    assert all(w.is_available for w in workers)


def test_request_agent_single_ownership_enforcement(db_session: Session, sample_customer_and_account):
    """Verify each RequestAgent can own only one active request at a time."""
    customer, account = sample_customer_and_account
    model = BankingSimulationModel()
    agent = model.get_request_agents()[0]

    req1 = Request(
        request_id="REQ-OWN-1",
        customer_id=customer.id,
        account_id=account.id,
        service_type=ServiceType.CHEQUE_BOOK,
        request_status=RequestStatus.CLASSIFIED,
    )
    req2 = Request(
        request_id="REQ-OWN-2",
        customer_id=customer.id,
        account_id=account.id,
        service_type=ServiceType.CHEQUE_BOOK,
        request_status=RequestStatus.CLASSIFIED,
    )
    db_session.add_all([req1, req2])
    db_session.flush()

    # Assign req1 to agent
    agent.accept_and_queue_request(db_session, req1)
    assert agent.is_available is False
    assert agent.current_request_id == "REQ-OWN-1"
    assert req1.request_status == RequestStatus.QUEUED

    # Attempting to assign req2 while agent is busy must fail
    with pytest.raises(RuntimeError):
        agent.accept_and_queue_request(db_session, req2)


def test_request_agent_release_and_completion_counter(db_session: Session, sample_customer_and_account):
    """Verify releasing an agent resets its state to IDLE and increments work counter."""
    customer, account = sample_customer_and_account
    model = BankingSimulationModel()
    agent = model.get_request_agents()[0]

    req = Request(
        request_id="REQ-REL-1",
        customer_id=customer.id,
        account_id=account.id,
        service_type=ServiceType.CHEQUE_BOOK,
        request_status=RequestStatus.CLASSIFIED,
    )
    db_session.add(req)
    db_session.flush()

    agent.accept_and_queue_request(db_session, req)
    assert agent.processing_status == "BUSY"

    # Complete and release
    agent.complete_and_release(db_session, req)
    assert agent.is_available is True
    assert agent.current_request_id is None
    assert agent.completed_work_count == 1
