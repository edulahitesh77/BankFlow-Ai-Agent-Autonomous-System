"""
BankFlow AI - Verification Agent Tests
Tests prerequisite verification, account relationship checks, and human review routing.
"""

import sys
import os
import pytest
from sqlalchemy.orm import Session

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.models.request import Request, ServiceType, RequestStatus
from app.models.customer import Customer
from app.models.account import Account
from app.models.user import User, UserRole
from app.auth.security import hash_password
from app.simulation.model import BankingSimulationModel


def test_verification_valid_account_prerequisites(db_session: Session, sample_customer_and_account):
    """Test verification agent verifies valid active account relationship."""
    customer, account = sample_customer_and_account
    model = BankingSimulationModel()
    verif = model.verification_agent

    req = Request(
        request_id="REQ-VERIF-01",
        customer_id=customer.id,
        account_id=account.id,
        service_type=ServiceType.CHEQUE_BOOK,
        request_status=RequestStatus.QUEUED,
        payload={"account_id": account.id, "number_of_leaves": 50},
    )
    db_session.add(req)
    db_session.flush()

    processed = verif.process_request(db_session, req)
    assert processed.request_status == RequestStatus.VERIFIED
    assert verif.completed_work_count == 1


def test_verification_account_application_human_review_referral(db_session: Session, sample_customer_and_account):
    """Test verification agent routes account pre-screenings to HUMAN_REVIEW."""
    customer, _ = sample_customer_and_account
    model = BankingSimulationModel()
    verif = model.verification_agent

    req = Request(
        request_id="REQ-VERIF-APP-01",
        customer_id=customer.id,
        service_type=ServiceType.ACCOUNT_APPLICATION,
        request_status=RequestStatus.QUEUED,
        payload={"applicant_name": "Applicant Beta", "email": "beta@bankflow.synthetic"},
    )
    db_session.add(req)
    db_session.flush()

    processed = verif.process_request(db_session, req)
    assert processed.request_status == RequestStatus.HUMAN_REVIEW
    assert processed.review_required is True


def test_verification_ownership_mismatch_rejection(db_session: Session, sample_customer_and_account):
    """Test verification agent rejects requests where account belongs to another customer."""
    customer, _ = sample_customer_and_account
    model = BankingSimulationModel()
    verif = model.verification_agent

    # Create another customer who owns the account
    user2 = User(
        username="user_mismatch_owner",
        email="mismatch_owner@bankflow.synthetic",
        password_hash=hash_password("Pass@2026!"),
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db_session.add(user2)
    db_session.flush()

    cust2 = Customer(
        user_id=user2.id,
        customer_code="CUST-OTHER-OWNER",
        full_name="Other Owner",
        email=user2.email,
    )
    db_session.add(cust2)
    db_session.flush()

    acc2 = Account(
        customer_id=cust2.id,
        synthetic_account_number="ACC-OTHER-001",
        account_type="SAVINGS",
        account_status="ACTIVE",
    )
    db_session.add(acc2)
    db_session.flush()

    # Customer tries to request cheque book on someone else's account
    req = Request(
        request_id="REQ-VERIF-MISMATCH",
        customer_id=customer.id,
        account_id=acc2.id,
        service_type=ServiceType.CHEQUE_BOOK,
        request_status=RequestStatus.QUEUED,
        payload={"account_id": acc2.id},
    )
    db_session.add(req)
    db_session.flush()

    processed = verif.process_request(db_session, req)
    assert processed.request_status == RequestStatus.REJECTED_INPUT
    assert processed.reason_code == "ACCOUNT_OWNERSHIP_MISMATCH"
