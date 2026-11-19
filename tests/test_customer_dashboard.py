"""
BankFlow AI - Phase 3 Customer Dashboard and Service Request Management Test Suite
Tests dashboard metrics, synthetic accounts, all 4 service request forms,
request tracking, request corrections, customer isolation, and security rules.
"""

import sys
import os
from typing import Tuple
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Ensure backend directory is in sys.path
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.main import app
from app.config import settings
from app.database import Base, get_db
from app.models.user import User, UserRole
from app.models.customer import Customer
from app.models.account import Account
from app.models.request import Request, ServiceType, RequestStatus
from app.models.audit_log import AuditLog
from app.auth.jwt_handler import create_access_token, clear_revoked_tokens
from app.auth.security import hash_password, login_rate_limiter
from app.services.user_service import UserService

# Test database setup
test_engine = create_engine(settings.test_database_url, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield


@pytest.fixture(scope="function")
def db_session() -> Session:
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> TestClient:
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    login_rate_limiter.reset_all()
    clear_revoked_tokens()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def customer_user(db_session: Session) -> Tuple[User, Customer, str]:
    """Helper creating a customer with an active JWT token."""
    user = User(
        username="cust_phase3_user",
        email="phase3.cust@bankflow.synthetic",
        password_hash=hash_password("Password@2026!"),
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    customer = Customer(
        user_id=user.id,
        customer_code="CUST-SYN-P3001",
        full_name="Phase 3 Customer",
        phone="+1-555-0301",
        email=user.email,
        branch_id="BR-MAIN-001",
    )
    db_session.add(customer)
    db_session.flush()

    token = create_access_token(user_id=user.id, role=user.role.value, username=user.username)
    return user, customer, token


@pytest.fixture(scope="function")
def customer_with_account(db_session: Session, customer_user) -> Tuple[User, Customer, Account, str]:
    """Helper creating customer with one synthetic account."""
    user, customer, token = customer_user
    account = Account(
        customer_id=customer.id,
        synthetic_account_number="SYN-ACC-9988776655",
        account_type="SAVINGS",
        account_status="ACTIVE",
        branch_id="BR-MAIN-001",
    )
    db_session.add(account)
    db_session.flush()
    return user, customer, account, token


# ============================================================================
# 1. CUSTOMER DASHBOARD & ACCOUNTS TESTS
# ============================================================================

def test_customer_dashboard_empty_state(client: TestClient, customer_user):
    """Test customer dashboard loads and properly reflects 0 accounts / 0 requests."""
    _, customer, token = customer_user

    response = client.get(
        "/api/customer/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["customer_name"] == customer.full_name
    assert data["customer_code"] == customer.customer_code
    assert data["summary"]["total_accounts"] == 0
    assert data["summary"]["total_requests"] == 0
    assert data["summary"]["pending_requests"] == 0
    assert data["summary"]["completed_requests"] == 0
    assert data["recent_requests"] == []


def test_customer_accounts_empty_state_and_creation(client: TestClient, customer_user):
    """Test customer accounts empty state and creation of synthetic demo account."""
    _, _, token = customer_user

    # 1. Initially empty
    res1 = client.get(
        "/api/customer/accounts",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res1.status_code == 200
    assert res1.json() == []

    # 2. Create synthetic account
    res2 = client.post(
        "/api/customer/accounts",
        headers={"Authorization": f"Bearer {token}"},
        json={"account_type": "CHECKING", "branch_id": "BR-MAIN-001"},
    )
    assert res2.status_code == 201
    new_acc = res2.json()
    assert new_acc["account_type"] == "CHECKING"
    assert new_acc["synthetic_account_number"].startswith("SYN-ACC-")

    # 3. Verify accounts list now contains the account
    res3 = client.get(
        "/api/customer/accounts",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res3.status_code == 200
    assert len(res3.json()) == 1
    assert res3.json()[0]["id"] == new_acc["id"]


# ============================================================================
# 2. ALL FOUR SERVICE REQUEST FORMS SUBMISSION TESTS
# ============================================================================

def test_submit_cheque_book_request(client: TestClient, customer_with_account, db_session: Session):
    """Test submitting Cheque Book Request with leaves validation."""
    _, customer, account, token = customer_with_account

    payload = {
        "service_type": "CHEQUE_BOOK",
        "account_id": account.id,
        "priority": "HIGH",
        "payload": {
            "account_id": account.id,
            "cheque_leaves": 50,
            "delivery_preference": "Standard Postal",
            "remarks": "Please deliver to home address",
        },
    }

    response = client.post(
        "/api/customer/requests",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert response.status_code == 201
    data = response.json()

    assert data["request_id"].startswith("BFA-REQ-")
    assert data["service_type"] == "CHEQUE_BOOK"
    assert data["request_status"] == "NEW"
    assert data["assignment_version"] == 0
    assert data["account_id"] == account.id
    assert data["payload"]["cheque_leaves"] == 50
    assert "1. Request Submitted" in data["current_stage"]

    # Verify audit log in database
    audit = db_session.query(AuditLog).filter(AuditLog.entity_id == data["request_id"]).first()
    assert audit is not None
    assert audit.action == "SERVICE_REQUEST_SUBMITTED"


def test_submit_cheque_book_invalid_leaves(client: TestClient, customer_with_account):
    """Test that invalid cheque leaves (e.g. 35) are rejected with 422."""
    _, _, account, token = customer_with_account

    payload = {
        "service_type": "CHEQUE_BOOK",
        "account_id": account.id,
        "payload": {
            "account_id": account.id,
            "cheque_leaves": 35,  # Invalid: must be 25, 50, or 100
            "delivery_preference": "Standard Postal",
        },
    }
    response = client.post(
        "/api/customer/requests",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert response.status_code == 422


def test_submit_debit_card_replacement_request(client: TestClient, customer_with_account):
    """Test submitting Debit Card Replacement request."""
    _, customer, account, token = customer_with_account

    payload = {
        "service_type": "DEBIT_CARD_REPLACEMENT",
        "account_id": account.id,
        "payload": {
            "account_id": account.id,
            "replacement_reason": "Damaged Card",
            "remarks": "Chip is peeling off",
        },
    }

    response = client.post(
        "/api/customer/requests",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert response.status_code == 201
    data = response.json()

    assert data["service_type"] == "DEBIT_CARD_REPLACEMENT"
    assert data["request_status"] == "NEW"
    assert data["payload"]["replacement_reason"] == "Damaged Card"


def test_submit_address_update_request(client: TestClient, customer_with_account):
    """Test submitting simulated Address Update request."""
    _, customer, account, token = customer_with_account

    payload = {
        "service_type": "ADDRESS_UPDATE",
        "account_id": account.id,
        "payload": {
            "account_id": account.id,
            "new_synthetic_address": "742 Evergreen Terrace",
            "city": "Springfield",
            "state": "Oregon",
            "postal_code": "97477",
            "reason_for_update": "Relocated to new residence",
        },
    }

    response = client.post(
        "/api/customer/requests",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert response.status_code == 201
    data = response.json()

    assert data["service_type"] == "ADDRESS_UPDATE"
    assert data["request_status"] == "NEW"
    assert data["payload"]["city"] == "Springfield"


def test_submit_account_application_prescreening(client: TestClient, customer_user):
    """Test submitting Account Application Pre-Screening."""
    _, customer, token = customer_user

    payload = {
        "service_type": "ACCOUNT_APPLICATION",
        "payload": {
            "applicant_name": "Alexander Vance",
            "email": "alex.vance@example.com",
            "phone": "+1-555-0188",
            "requested_account_type": "SAVINGS",
            "branch_preference": "Central Downtown Branch",
            "remarks": "Applying for secondary savings pool",
        },
    }

    response = client.post(
        "/api/customer/requests",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert response.status_code == 201
    data = response.json()

    assert data["service_type"] == "ACCOUNT_APPLICATION"
    assert data["request_status"] == "NEW"
    assert data["payload"]["requested_account_type"] == "SAVINGS"


# ============================================================================
# 3. CUSTOMER DATA ISOLATION & OWNERSHIP TESTS
# ============================================================================

def test_customer_cannot_use_another_customers_account(client: TestClient, db_session: Session, customer_user):
    """Verify customer cannot submit requests against an account belonging to someone else."""
    _, customer1, token1 = customer_user

    # Create another customer and account
    user2 = User(
        username="other_cust_99",
        email="other.cust99@bankflow.synthetic",
        role=UserRole.CUSTOMER,
    )
    db_session.add(user2)
    db_session.flush()

    customer2 = Customer(
        user_id=user2.id,
        customer_code="CUST-SYN-OTHER",
        full_name="Other Customer",
        email=user2.email,
    )
    db_session.add(customer2)
    db_session.flush()

    account2 = Account(
        customer_id=customer2.id,
        synthetic_account_number="SYN-ACC-OTHER-1234",
        account_type="SAVINGS",
        account_status="ACTIVE",
    )
    db_session.add(account2)
    db_session.flush()

    # Customer 1 attempts to submit cheque request against account 2
    payload = {
        "service_type": "CHEQUE_BOOK",
        "account_id": account2.id,
        "payload": {
            "account_id": account2.id,
            "cheque_leaves": 25,
            "delivery_preference": "Branch Pickup",
        },
    }
    response = client.post(
        "/api/customer/requests",
        headers={"Authorization": f"Bearer {token1}"},
        json=payload,
    )
    assert response.status_code == 400
    assert "does not belong to your customer profile" in response.json()["detail"]


def test_customer_cannot_see_another_customers_requests(client: TestClient, db_session: Session, customer_user):
    """Verify customer cannot see another customer's requests via list or direct ID."""
    _, customer1, token1 = customer_user

    # Create request for another customer
    user2 = User(
        username="cust_isolated_2",
        email="isolated2@bankflow.synthetic",
        role=UserRole.CUSTOMER,
    )
    db_session.add(user2)
    db_session.flush()
    customer2 = Customer(user_id=user2.id, customer_code="CUST-SYN-ISO2", full_name="Customer Two", email=user2.email)
    db_session.add(customer2)
    db_session.flush()

    req2 = Request(
        request_id="BFA-REQ-2026-SECRET",
        customer_id=customer2.id,
        service_type=ServiceType.CHEQUE_BOOK,
        request_status=RequestStatus.NEW,
    )
    db_session.add(req2)
    db_session.flush()

    # 1. Customer 1 lists requests: secret request must not appear
    res_list = client.get(
        "/api/customer/requests",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert res_list.status_code == 200
    request_ids = [r["request_id"] for r in res_list.json()["items"]]
    assert "BFA-REQ-2026-SECRET" not in request_ids

    # 2. Customer 1 direct fetch of secret request ID: returns HTTP 404
    res_detail = client.get(
        "/api/customer/requests/BFA-REQ-2026-SECRET",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert res_detail.status_code == 404


# ============================================================================
# 4. REQUEST TRACKING & EXCEPTION STATES TESTS
# ============================================================================

def test_request_tracking_and_exception_stages(client: TestClient, db_session: Session, customer_user):
    """Test detailed request tracking and visual progress stages for normal & exception states."""
    _, customer, token = customer_user

    # Create requests in diverse statuses
    req_new = Request(
        request_id="BFA-REQ-TRACK-NEW",
        customer_id=customer.id,
        service_type=ServiceType.CHEQUE_BOOK,
        request_status=RequestStatus.NEW,
    )
    req_corr = Request(
        request_id="BFA-REQ-TRACK-CORR",
        customer_id=customer.id,
        service_type=ServiceType.DEBIT_CARD_REPLACEMENT,
        request_status=RequestStatus.NEEDS_CORRECTION,
        reason_code="INVALID_DELIVERY_PREFERENCE",
    )
    req_rev = Request(
        request_id="BFA-REQ-TRACK-REV",
        customer_id=customer.id,
        service_type=ServiceType.ADDRESS_UPDATE,
        request_status=RequestStatus.HUMAN_REVIEW,
        review_required=True,
    )
    db_session.add_all([req_new, req_corr, req_rev])
    db_session.flush()

    # Check NEW request stage
    r1 = client.get(f"/api/customer/requests/{req_new.request_id}", headers={"Authorization": f"Bearer {token}"})
    assert r1.status_code == 200
    assert "1. Request Submitted" in r1.json()["current_stage"]

    # Check NEEDS_CORRECTION stage
    r2 = client.get(f"/api/customer/requests/{req_corr.request_id}", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    assert "Action Required" in r2.json()["current_stage"]
    assert r2.json()["reason_code"] == "INVALID_DELIVERY_PREFERENCE"

    # Check HUMAN_REVIEW stage
    r3 = client.get(f"/api/customer/requests/{req_rev.request_id}", headers={"Authorization": f"Bearer {token}"})
    assert r3.status_code == 200
    assert "Supervisor Review" in r3.json()["current_stage"]


# ============================================================================
# 5. REQUEST CORRECTION WORKFLOW TESTS
# ============================================================================

def test_request_correction_workflow(client: TestClient, db_session: Session, customer_with_account):
    """Test submitting corrections on a request in NEEDS_CORRECTION status."""
    _, customer, account, token = customer_with_account

    # 1. Create a request in NEEDS_CORRECTION state
    req = Request(
        request_id="BFA-REQ-CORR-001",
        customer_id=customer.id,
        account_id=account.id,
        service_type=ServiceType.CHEQUE_BOOK,
        request_status=RequestStatus.NEEDS_CORRECTION,
        assignment_version=1,
        reason_code="PLEASE_SELECT_STANDARD_LEAVES",
        payload={"account_id": account.id, "cheque_leaves": 25, "delivery_preference": "Standard Postal"},
    )
    db_session.add(req)
    db_session.flush()

    # 2. Submit correction
    correction_payload = {
        "payload": {
            "account_id": account.id,
            "cheque_leaves": 100,  # Updated to 100
            "delivery_preference": "Branch Pickup",
        },
        "correction_notes": "Updated cheque leaves count to 100 as requested.",
    }
    response = client.put(
        f"/api/customer/requests/{req.request_id}/correction",
        headers={"Authorization": f"Bearer {token}"},
        json=correction_payload,
    )
    assert response.status_code == 200
    updated = response.json()

    # Status must return to NEW
    assert updated["request_status"] == "NEW"
    # Version must increment
    assert updated["assignment_version"] == 2
    # Payload must reflect correction
    assert updated["payload"]["cheque_leaves"] == 100
    assert updated["payload"]["customer_correction_notes"] == "Updated cheque leaves count to 100 as requested."


def test_request_correction_rejected_when_not_needs_correction(client: TestClient, db_session: Session, customer_user):
    """Test that customer cannot submit corrections when request is NEW, IN_SERVICE, or COMPLETED."""
    _, customer, token = customer_user

    req = Request(
        request_id="BFA-REQ-NO-CORR",
        customer_id=customer.id,
        service_type=ServiceType.ACCOUNT_APPLICATION,
        request_status=RequestStatus.NEW,  # Not in NEEDS_CORRECTION
    )
    db_session.add(req)
    db_session.flush()

    correction_payload = {
        "payload": {
            "applicant_name": "Test",
            "email": "test@test.com",
            "phone": "+1-555-0100",
            "requested_account_type": "SAVINGS",
            "branch_preference": "Main",
        }
    }
    response = client.put(
        f"/api/customer/requests/{req.request_id}/correction",
        headers={"Authorization": f"Bearer {token}"},
        json=correction_payload,
    )
    assert response.status_code == 400
    assert "Corrections are only permitted when status is 'NEEDS_CORRECTION'" in response.json()["detail"]


# ============================================================================
# 6. PROFILE UPDATE TESTS
# ============================================================================

def test_customer_profile_update_permitted_fields(client: TestClient, customer_user):
    """Test updating permitted profile fields (full_name, phone)."""
    _, customer, token = customer_user

    payload = {
        "full_name": "Updated Customer Name",
        "phone": "+1-555-9988",
    }
    response = client.put(
        "/api/customer/profile",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Customer Name"
    assert data["phone"] == "+1-555-9988"
    assert data["customer_code"] == customer.customer_code  # Unchanged
    assert data["email"] == customer.email  # Unchanged


# ============================================================================
# 7. SECURITY & ROLE TESTS
# ============================================================================

def test_bank_employee_cannot_access_customer_dashboard_endpoints(client: TestClient, db_session: Session):
    """Verify that a BANK_EMPLOYEE receives HTTP 403 when trying to access customer dashboard or submit requests."""
    _, employee = UserService.provision_bank_employee(
        db=db_session,
        username="bank_staff_p3",
        email="bank.staff.p3@bankflow.synthetic",
        password="StaffPassword@2026!",
        employee_code="EMP-SYN-P399",
        full_name="Bank Staff Person",
    )
    token = create_access_token(user_id=employee.user_id, role="BANK_EMPLOYEE", username=employee.user.username)

    # 1. Dashboard
    res1 = client.get("/api/customer/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert res1.status_code == 403

    # 2. Accounts
    res2 = client.get("/api/customer/accounts", headers={"Authorization": f"Bearer {token}"})
    assert res2.status_code == 403

    # 3. Requests
    res3 = client.get("/api/customer/requests", headers={"Authorization": f"Bearer {token}"})
    assert res3.status_code == 403
