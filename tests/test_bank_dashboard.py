"""
BankFlow AI - Phase 4 Bank Employee Dashboard and Request Management Test Suite
Tests bank employee statistics, all request views, pending requests, human review decisions,
correction workflows, customer record inspection, audit logs, and strict RBAC isolation.
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
from app.models.employee import Employee
from app.models.account import Account
from app.models.request import Request, ServiceType, RequestStatus
from app.models.review_record import ReviewRecord, ReviewDecision
from app.models.correction_record import CorrectionRecord
from app.models.notification import Notification
from app.models.audit_log import AuditLog
from app.auth.jwt_handler import create_access_token
from app.auth.security import hash_password

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

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def create_test_employee(db: Session, suffix: str = "1") -> Tuple[User, Employee, str]:
    """Helper to provision a test bank employee and return user, employee, and JWT token."""
    username = f"employee_officer_{suffix}"
    email = f"officer_{suffix}@bankflow.synthetic"
    hashed_pw = hash_password("BankAdmin@2026!")

    user = User(
        username=username,
        email=email,
        password_hash=hashed_pw,
        role=UserRole.BANK_EMPLOYEE,
        is_active=True,
    )
    db.add(user)
    db.flush()

    emp = Employee(
        user_id=user.id,
        employee_code=f"EMP-TEST-{suffix.zfill(4)}",
        full_name=f"Officer Test {suffix}",
        department="Operations",
        designation="Senior Reviewer",
        branch_id="BR-MAIN-001",
    )
    db.add(emp)
    db.flush()

    token = create_access_token(
        user_id=user.id,
        role=user.role.value,
        username=user.username,
    )
    return user, emp, token


def create_test_customer(db: Session, suffix: str = "1") -> Tuple[User, Customer, str]:
    """Helper to provision a test customer and return user, customer, and JWT token."""
    username = f"cust_user_{suffix}"
    email = f"cust_{suffix}@bankflow.synthetic"
    hashed_pw = hash_password("SecurePass@2026!")

    user = User(
        username=username,
        email=email,
        password_hash=hashed_pw,
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db.add(user)
    db.flush()

    customer = Customer(
        user_id=user.id,
        customer_code=f"CUST-TEST-{suffix.zfill(4)}",
        full_name=f"Customer Test {suffix}",
        phone=f"+1-555-01{suffix.zfill(2)}",
        email=email,
        branch_id="BR-MAIN-001",
    )
    db.add(customer)
    db.flush()

    token = create_access_token(
        user_id=user.id,
        role=user.role.value,
        username=user.username,
    )
    return user, customer, token


def create_test_account(db: Session, customer: Customer, acc_num: str = "ACC-SYN-1001") -> Account:
    """Helper to provision a synthetic account."""
    acc = Account(
        customer_id=customer.id,
        synthetic_account_number=acc_num,
        account_type="SAVINGS",
        account_status="ACTIVE",
        branch_id="BR-MAIN-001",
    )
    db.add(acc)
    db.flush()
    return acc


def create_test_request(
    db: Session,
    customer: Customer,
    service_type: ServiceType = ServiceType.CHEQUE_BOOK,
    status: RequestStatus = RequestStatus.NEW,
    req_code: str = "BFA-REQ-TEST-001",
    review_required: bool = False,
    priority: str = "MEDIUM",
    account: Account = None,
) -> Request:
    """Helper to provision a request with test parameters."""
    req = Request(
        request_id=req_code,
        customer_id=customer.id,
        account_id=account.id if account else None,
        service_type=service_type,
        request_status=status,
        priority=priority,
        assignment_version=0,
        review_required=review_required,
        payload={"notes": "Test payload parameter"},
    )
    db.add(req)
    db.flush()
    return req


# ============================================================================
# 1. BANK DASHBOARD OVERVIEW TESTS
# ============================================================================

def test_bank_dashboard_metrics(client: TestClient, db_session: Session):
    """Test that bank dashboard calculates real metrics, distributions, and demand."""
    _, _, emp_token = create_test_employee(db_session, "dash")
    _, cust, _ = create_test_customer(db_session, "dash")
    acc = create_test_account(db_session, cust, "ACC-SYN-DASH-1")

    # Seed diverse requests
    create_test_request(db_session, cust, ServiceType.CHEQUE_BOOK, RequestStatus.NEW, "REQ-D-1", account=acc)
    create_test_request(db_session, cust, ServiceType.CHEQUE_BOOK, RequestStatus.COMPLETED, "REQ-D-2", account=acc)
    create_test_request(db_session, cust, ServiceType.DEBIT_CARD_REPLACEMENT, RequestStatus.NEEDS_CORRECTION, "REQ-D-3", account=acc)
    create_test_request(db_session, cust, ServiceType.ADDRESS_UPDATE, RequestStatus.REJECTED_INPUT, "REQ-D-4")
    create_test_request(db_session, cust, ServiceType.ACCOUNT_APPLICATION, RequestStatus.HUMAN_REVIEW, "REQ-D-5", review_required=True)
    db_session.commit()

    response = client.get(
        "/api/bank/dashboard",
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert response.status_code == 200
    data = response.json()

    summary = data["summary"]
    assert summary["total_requests"] >= 5
    assert summary["new_requests"] >= 1
    assert summary["completed_requests"] >= 1
    assert summary["needs_correction_requests"] >= 1
    assert summary["rejected_requests"] >= 1
    assert summary["human_review_requests"] >= 1
    assert summary["total_customers"] >= 1
    assert summary["total_accounts"] >= 1

    # Verify distributions
    assert "CHEQUE_BOOK" in data["request_distribution"]
    assert data["request_distribution"]["CHEQUE_BOOK"] >= 2
    assert "NEW" in data["status_distribution"]
    assert len(data["service_demand"]) == 4


# ============================================================================
# 2. REQUEST MANAGEMENT & FILTERING TESTS
# ============================================================================

def test_get_all_requests_and_filters(client: TestClient, db_session: Session):
    """Test listing requests with filtering by status, service type, and pagination."""
    _, _, emp_token = create_test_employee(db_session, "filt")
    _, cust, _ = create_test_customer(db_session, "filt")

    create_test_request(db_session, cust, ServiceType.CHEQUE_BOOK, RequestStatus.NEW, "REQ-FILT-1")
    create_test_request(db_session, cust, ServiceType.ADDRESS_UPDATE, RequestStatus.COMPLETED, "REQ-FILT-2")
    db_session.commit()

    # Filter by status NEW
    resp_new = client.get(
        "/api/bank/requests?status=NEW",
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert resp_new.status_code == 200
    items_new = resp_new.json()["items"]
    assert all(r["request_status"] == "NEW" for r in items_new)

    # Filter by service_type ADDRESS_UPDATE
    resp_addr = client.get(
        "/api/bank/requests?service_type=ADDRESS_UPDATE",
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert resp_addr.status_code == 200
    items_addr = resp_addr.json()["items"]
    assert all(r["service_type"] == "ADDRESS_UPDATE" for r in items_addr)


def test_search_requests(client: TestClient, db_session: Session):
    """Test searching requests by Request ID, customer code, or customer name."""
    _, _, emp_token = create_test_employee(db_session, "search")
    _, cust, _ = create_test_customer(db_session, "search")

    create_test_request(db_session, cust, ServiceType.CHEQUE_BOOK, RequestStatus.NEW, "REQ-UNIQUE-XYZ-999")
    db_session.commit()

    # Search by unique request ID
    resp = client.get(
        "/api/bank/requests?search=UNIQUE-XYZ",
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["request_id"] == "REQ-UNIQUE-XYZ-999"

    # Search by customer name
    resp_name = client.get(
        f"/api/bank/requests?search={cust.full_name}",
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert resp_name.status_code == 200
    assert resp_name.json()["total"] >= 1


def test_get_request_details_and_audit(client: TestClient, db_session: Session):
    """Test retrieving request details and verifying that viewing records an audit entry."""
    _, emp, emp_token = create_test_employee(db_session, "detail")
    _, cust, _ = create_test_customer(db_session, "detail")
    acc = create_test_account(db_session, cust, "ACC-SYN-DET-1")
    req = create_test_request(db_session, cust, ServiceType.CHEQUE_BOOK, RequestStatus.NEW, "REQ-DETAIL-100", account=acc)
    db_session.commit()

    resp = client.get(
        f"/api/bank/requests/{req.request_id}",
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["request_id"] == req.request_id
    assert data["customer_code"] == cust.customer_code
    assert data["customer_name"] == cust.full_name
    assert data["account_number"] == acc.synthetic_account_number

    # Verify audit log was recorded for viewing
    view_log = (
        db_session.query(AuditLog)
        .filter(
            AuditLog.entity_id == req.request_id,
            AuditLog.action == "EMPLOYEE_VIEWED_REQUEST",
        )
        .first()
    )
    assert view_log is not None
    assert str(emp.employee_code) in view_log.description


# ============================================================================
# 3. PENDING & QUEUE MANAGEMENT TESTS
# ============================================================================

def test_pending_requests_queue(client: TestClient, db_session: Session):
    """Test retrieving requests awaiting processing via /requests/pending."""
    _, _, emp_token = create_test_employee(db_session, "pend")
    _, cust, _ = create_test_customer(db_session, "pend")

    create_test_request(db_session, cust, ServiceType.CHEQUE_BOOK, RequestStatus.NEW, "REQ-PEND-1")
    create_test_request(db_session, cust, ServiceType.DEBIT_CARD_REPLACEMENT, RequestStatus.QUEUED, "REQ-PEND-2")
    create_test_request(db_session, cust, ServiceType.ADDRESS_UPDATE, RequestStatus.COMPLETED, "REQ-NOT-PEND")
    db_session.commit()

    resp = client.get(
        "/api/bank/requests/pending",
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    req_ids = [r["request_id"] for r in items]
    assert "REQ-PEND-1" in req_ids
    assert "REQ-PEND-2" in req_ids
    assert "REQ-NOT-PEND" not in req_ids


# ============================================================================
# 4. HUMAN REVIEW WORKFLOW TESTS
# ============================================================================

def test_human_review_workflow_approval(client: TestClient, db_session: Session):
    """Test reviewing a request with REVIEW_COMPLETED decision."""
    _, emp, emp_token = create_test_employee(db_session, "rev1")
    _, cust, _ = create_test_customer(db_session, "rev1")
    req = create_test_request(
        db_session,
        cust,
        ServiceType.CHEQUE_BOOK,
        RequestStatus.HUMAN_REVIEW,
        "REQ-HR-APPROVE",
        review_required=True,
    )
    db_session.commit()

    # Verify appears in human review list
    list_resp = client.get(
        "/api/bank/requests/human-review",
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert list_resp.status_code == 200
    items = list_resp.json()["items"]
    assert any(r["request_id"] == "REQ-HR-APPROVE" for r in items)

    # Submit REVIEW_COMPLETED decision
    review_payload = {
        "decision": "REVIEW_COMPLETED",
        "internal_note": "Identity documents verified against branch records. Approved for dispatch.",
    }
    rev_resp = client.post(
        f"/api/bank/requests/{req.request_id}/review",
        json=review_payload,
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert rev_resp.status_code == 200
    data = rev_resp.json()
    assert data["review_required"] is False
    assert data["request_status"] == "VERIFIED"
    assert len(data["reviews"]) >= 1
    assert data["reviews"][0]["review_decision"] == "REVIEW_COMPLETED"
    assert data["reviews"][0]["employee_code"] == emp.employee_code


def test_human_review_workflow_rejection(client: TestClient, db_session: Session):
    """Test rejecting a request during human review."""
    _, _, emp_token = create_test_employee(db_session, "rev2")
    _, cust, _ = create_test_customer(db_session, "rev2")
    req = create_test_request(
        db_session,
        cust,
        ServiceType.DEBIT_CARD_REPLACEMENT,
        RequestStatus.HUMAN_REVIEW,
        "REQ-HR-REJECT",
        review_required=True,
    )
    db_session.commit()

    review_payload = {
        "decision": "REVIEW_REJECTED",
        "internal_note": "Card was previously reported fraudulently active. Replaced card cannot be reissued without in-person identity verification.",
        "reason_code": "SUSPECTED_COMPROMISE",
    }
    rev_resp = client.post(
        f"/api/bank/requests/{req.request_id}/review",
        json=review_payload,
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert rev_resp.status_code == 200
    data = rev_resp.json()
    assert data["request_status"] == "REJECTED_INPUT"
    assert data["review_required"] is False

    # Verify notification created for customer
    notif = (
        db_session.query(Notification)
        .filter(Notification.customer_id == cust.id, Notification.request_id == req.id)
        .first()
    )
    assert notif is not None
    assert "Request Not Approved" in notif.notification_title


def test_human_review_escalation(client: TestClient, db_session: Session):
    """Test escalating a request to senior supervisor."""
    _, _, emp_token = create_test_employee(db_session, "rev3")
    _, cust, _ = create_test_customer(db_session, "rev3")
    req = create_test_request(
        db_session,
        cust,
        ServiceType.CHEQUE_BOOK,
        RequestStatus.HUMAN_REVIEW,
        "REQ-HR-ESC",
        review_required=True,
    )
    db_session.commit()

    review_payload = {
        "decision": "ESCALATED",
        "internal_note": "Request exceeds standard cheque threshold. Escalating to branch head.",
    }
    rev_resp = client.post(
        f"/api/bank/requests/{req.request_id}/review",
        json=review_payload,
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert rev_resp.status_code == 200
    data = rev_resp.json()
    assert data["review_required"] is True
    assert data["priority"] == "HIGH"


# ============================================================================
# 5. CORRECTION WORKFLOW & IN-APP NOTIFICATION TESTS
# ============================================================================

def test_request_correction_workflow(client: TestClient, db_session: Session):
    """
    Test employee requesting correction:
    1. Employee flags request as NEEDS_CORRECTION.
    2. Notification is generated for customer.
    3. Customer sees notification and resubmits correction.
    4. Version increments and status resets to NEW.
    """
    _, emp, emp_token = create_test_employee(db_session, "corr")
    _, cust, cust_token = create_test_customer(db_session, "corr")
    acc = create_test_account(db_session, cust, "ACC-SYN-CORR-1")
    req = create_test_request(
        db_session,
        cust,
        ServiceType.ADDRESS_UPDATE,
        RequestStatus.NEW,
        "REQ-CORR-001",
        account=acc,
    )
    db_session.commit()

    # Employee submits correction request
    corr_payload = {
        "correction_reason": "Proof of Address Illegible",
        "customer_instruction": "Please provide a valid utility bill or lease agreement with visible address header.",
    }
    resp = client.post(
        f"/api/bank/requests/{req.request_id}/request-correction",
        json=corr_payload,
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["request_status"] == "NEEDS_CORRECTION"
    assert data["reason_code"] == "Proof of Address Illegible"
    assert len(data["corrections"]) >= 1
    assert data["corrections"][0]["employee_code"] == emp.employee_code

    # Customer checks notifications
    cust_notif_resp = client.get(
        "/api/customer/notifications",
        headers={"Authorization": f"Bearer {cust_token}"},
    )
    assert cust_notif_resp.status_code == 200
    notif_data = cust_notif_resp.json()
    assert notif_data["total"] >= 1
    assert any(n["request_id"] == req.id for n in notif_data["items"])

    # Customer submits correction via Phase 3 correction endpoint
    update_payload = {
        "payload": {
            "account_id": acc.id,
            "new_synthetic_address": "456 Updated Boulevard",
            "city": "Metropolis",
            "state": "NY",
            "postal_code": "10002",
            "reason_for_update": "Resubmitted with clear utility bill document reference",
        },
        "correction_note": "Attached updated synthetic utility statement ref #UTL-9988.",
    }
    cust_resubmit_resp = client.put(
        f"/api/customer/requests/{req.request_id}/correction",
        json=update_payload,
        headers={"Authorization": f"Bearer {cust_token}"},
    )
    assert cust_resubmit_resp.status_code == 200
    resub_data = cust_resubmit_resp.json()
    assert resub_data["request_status"] == "NEW"
    assert resub_data["assignment_version"] == 1


# ============================================================================
# 6. CUSTOMER RECORDS & PRIVACY TESTS
# ============================================================================

def test_customer_records_list_and_details(client: TestClient, db_session: Session):
    """Test employee searching customer records, inspecting accounts, and ensuring secrets are omitted."""
    _, _, emp_token = create_test_employee(db_session, "rec")
    _, cust, _ = create_test_customer(db_session, "rec")
    create_test_account(db_session, cust, "ACC-SYN-REC-1")
    create_test_request(db_session, cust, ServiceType.CHEQUE_BOOK, RequestStatus.NEW, "REQ-REC-1")
    db_session.commit()

    # Search customers
    resp = client.get(
        f"/api/bank/customers?search={cust.customer_code}",
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    cust_item = data["items"][0]
    assert cust_item["customer_code"] == cust.customer_code
    assert cust_item["total_accounts"] >= 1
    assert cust_item["total_requests"] >= 1
    # Ensure sensitive credentials are absent
    assert "password" not in cust_item
    assert "password_hash" not in cust_item

    # Customer details
    detail_resp = client.get(
        f"/api/bank/customers/{cust.id}",
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert detail_resp.status_code == 200
    det = detail_resp.json()
    assert det["customer_code"] == cust.customer_code
    assert len(det["accounts"]) >= 1
    assert len(det["requests"]) >= 1


# ============================================================================
# 7. AUDIT LOGS & AGENT MONITORING TESTS
# ============================================================================

def test_audit_logs_endpoint(client: TestClient, db_session: Session):
    """Test retrieving compliance audit logs."""
    _, _, emp_token = create_test_employee(db_session, "audit")
    _, cust, _ = create_test_customer(db_session, "audit")

    # Trigger action to generate audit log
    req = create_test_request(db_session, cust, ServiceType.CHEQUE_BOOK, RequestStatus.NEW, "REQ-AUDIT-LOG-1")
    db_session.commit()

    # View request to trigger EMPLOYEE_VIEWED_REQUEST audit log
    client.get(
        f"/api/bank/requests/{req.request_id}",
        headers={"Authorization": f"Bearer {emp_token}"},
    )

    resp = client.get(
        "/api/bank/audit-logs?entity_type=REQUEST",
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert any(log["action"] == "EMPLOYEE_VIEWED_REQUEST" for log in data["items"])


def test_agent_monitoring_placeholder(client: TestClient, db_session: Session):
    """Test agent monitoring endpoint returns active Phase 5 Multi-Agent Swarm."""
    _, _, emp_token = create_test_employee(db_session, "agent")

    resp = client.get(
        "/api/bank/agents",
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "agents" in data
    assert "total" in data
    assert data["total"] >= 9


# ============================================================================
# 8. SECURITY & RBAC TESTS
# ============================================================================

def test_bank_endpoints_rbac(client: TestClient, db_session: Session):
    """Test that unauthenticated users and customers are forbidden from bank endpoints."""
    _, _, cust_token = create_test_customer(db_session, "sec")

    # 1. Unauthenticated request -> HTTP 401
    resp_unauth = client.get("/api/bank/dashboard")
    assert resp_unauth.status_code == 401

    # 2. Customer attempting to access bank dashboard -> HTTP 403
    resp_forbidden = client.get(
        "/api/bank/dashboard",
        headers={"Authorization": f"Bearer {cust_token}"},
    )
    assert resp_forbidden.status_code == 403

    # 3. Customer attempting to access bank requests -> HTTP 403
    resp_forbidden2 = client.get(
        "/api/bank/requests",
        headers={"Authorization": f"Bearer {cust_token}"},
    )
    assert resp_forbidden2.status_code == 403
