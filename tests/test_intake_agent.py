"""
BankFlow AI - Intake Agent Tests
Tests request validation, field completeness, classification, and exception routing.
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


def test_intake_valid_cheque_book_request(db_session: Session, sample_customer_and_account):
    """Test intake agent classifies a valid cheque book request."""
    customer, account = sample_customer_and_account
    model = BankingSimulationModel()
    intake = model.intake_agent

    req = Request(
        request_id="REQ-INTAKE-01",
        customer_id=customer.id,
        account_id=account.id,
        service_type=ServiceType.CHEQUE_BOOK,
        request_status=RequestStatus.NEW,
        payload={"account_id": account.id, "number_of_leaves": 50},
    )
    db_session.add(req)
    db_session.flush()

    processed = intake.process_request(db_session, req)
    assert processed.request_status == RequestStatus.CLASSIFIED
    assert intake.completed_work_count == 1


def test_intake_missing_leaves_needs_correction(db_session: Session, sample_customer_and_account):
    """Test intake agent flags missing or invalid leaf counts as NEEDS_CORRECTION."""
    customer, account = sample_customer_and_account
    model = BankingSimulationModel()
    intake = model.intake_agent

    req = Request(
        request_id="REQ-INTAKE-02",
        customer_id=customer.id,
        account_id=account.id,
        service_type=ServiceType.CHEQUE_BOOK,
        request_status=RequestStatus.NEW,
        payload={"account_id": account.id, "number_of_leaves": 42},  # 42 is invalid
    )
    db_session.add(req)
    db_session.flush()

    processed = intake.process_request(db_session, req)
    assert processed.request_status == RequestStatus.NEEDS_CORRECTION
    assert processed.reason_code == "INVALID_LEAF_SELECTION"


def test_intake_lost_card_security_human_review(db_session: Session, sample_customer_and_account):
    """Test intake agent flags lost card replacement for human supervisory review."""
    customer, account = sample_customer_and_account
    model = BankingSimulationModel()
    intake = model.intake_agent

    req = Request(
        request_id="REQ-INTAKE-03",
        customer_id=customer.id,
        account_id=account.id,
        service_type=ServiceType.DEBIT_CARD_REPLACEMENT,
        request_status=RequestStatus.NEW,
        payload={"account_id": account.id, "replacement_reason": "lost"},
    )
    db_session.add(req)
    db_session.flush()

    processed = intake.process_request(db_session, req)
    assert processed.request_status == RequestStatus.HUMAN_REVIEW
    assert processed.reason_code == "SECURITY_CARD_REPLACEMENT"


def test_intake_missing_address_fields(db_session: Session, sample_customer_and_account):
    """Test intake agent rejects incomplete address payloads."""
    customer, account = sample_customer_and_account
    model = BankingSimulationModel()
    intake = model.intake_agent

    req = Request(
        request_id="REQ-INTAKE-04",
        customer_id=customer.id,
        account_id=account.id,
        service_type=ServiceType.ADDRESS_UPDATE,
        request_status=RequestStatus.NEW,
        payload={"account_id": account.id, "city": "Metropolis"},  # Missing street, state, postal
    )
    db_session.add(req)
    db_session.flush()

    processed = intake.process_request(db_session, req)
    assert processed.request_status == RequestStatus.NEEDS_CORRECTION
    assert processed.reason_code == "INCOMPLETE_ADDRESS_FIELDS"
