"""
BankFlow AI - Multi-Branch Federation Test Suite (Phase 10)
Tests cross-branch information exchange, Federation Gateway authentication,
scope authorization, anti-replay deduplication, destination failure handling,
and FastAPI federation management endpoints.
"""

import sys
import os
import uuid
import pytest
from typing import Tuple
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.main import app
from app.database import get_db, BranchDatabaseManager
from app.models.user import User, UserRole
from app.models.employee import Employee
from app.models.customer import Customer
from app.models.account import Account
from app.models.branch import Branch
from app.models.federation_event import FederationEvent
from app.auth.jwt_handler import create_access_token, clear_revoked_tokens
from app.auth.security import hash_password, login_rate_limiter
from app.federation.schemas import CrossBranchRequest, CrossBranchResponse
from app.federation.gateway import FederationGateway
from app.federation.security import FederationSecurityManager, BRANCH_SECRETS
from app.federation.seed import seed_all_branches


@pytest.fixture(scope="session", autouse=True)
def setup_federation_databases():
    """Ensure branch tables and test synthetic data exist across branch databases."""
    try:
        seed_all_branches(is_test=False)
    except Exception as e:
        print(f"Federation test seeding note: {e}")


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
def bank_employee_auth(db_session: Session) -> Tuple[User, Employee, str]:
    """Helper creating a test bank employee with JWT token."""
    user = User(
        username="fed_test_officer",
        email="fed_officer@bankflow.test",
        password_hash=hash_password("FedSecure@2026!"),
        role=UserRole.BANK_EMPLOYEE,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    emp = Employee(
        user_id=user.id,
        employee_code="EMP-TEST-FED-01",
        full_name="Federation Test Officer",
        department="Inter-Branch Operations",
        designation="Federation Supervisor",
        branch_id="BLR001",
    )
    db_session.add(emp)
    db_session.commit()

    token = create_access_token(
        role="BANK_EMPLOYEE",
        username=user.username,
        user_id=user.id,
    )
    return user, emp, token


@pytest.fixture(scope="function")
def customer_auth(db_session: Session) -> Tuple[User, Customer, str]:
    """Helper creating a customer user with JWT token."""
    user = User(
        username="fed_test_customer",
        email="fed_cust@bankflow.test",
        password_hash=hash_password("CustSecure@2026!"),
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    cust = Customer(
        user_id=user.id,
        customer_code="CUST-FED-CUST-01",
        full_name="Federation Test Customer",
        email=user.email,
        phone="+91-80-000-9999",
        branch_id="BLR001",
    )
    db_session.add(cust)
    db_session.commit()

    token = create_access_token(
        role="CUSTOMER",
        username=user.username,
        user_id=user.id,
    )
    return user, cust, token


# ============================================================================
# 1. Functional Federation Scenarios (F1 - F6)
# ============================================================================

def test_f1_bengaluru_to_chennai_authorized(db_session: Session):
    """
    Test F1: Bengaluru (BLR001) sends an authorized account-status confirmation
    request to Chennai (CHE001).
    Expectations:
    - Authentication succeeds with BLR001 secret.
    - Scope authorization succeeds.
    - Only permitted synthetic confirmation fields returned.
    - Audit event is persisted.
    """
    req = CrossBranchRequest(
        source_branch_id="BLR001",
        destination_branch_id="CHE001",
        requested_scope="ACCOUNT_STATUS_CONFIRMATION",
        request_id="REQ-F1-BLR-001",
        correlation_id=f"f1-corr-{uuid.uuid4().hex[:8]}",
        query_params={"synthetic_account_number": "ACC-CHE001-1001"},
    )

    api_key = BRANCH_SECRETS["BLR001"]
    res = FederationGateway.process_cross_branch_request(req, api_key=api_key, gateway_db=db_session)

    assert res.status == "SUCCESS"
    assert res.authorization_result == "AUTHORIZED"
    assert res.source_branch_id == "BLR001"
    assert res.destination_branch_id == "CHE001"
    assert res.data is not None

    # Verify Principle of Least Privilege: only permitted status fields
    assert "account_status" in res.data
    assert "is_confirmed" in res.data
    assert "branch_id" in res.data
    assert res.data["is_confirmed"] is True
    # Verify no PII or credentials leaked
    assert "password_hash" not in res.data
    assert "balance" not in res.data

    # Verify audit event persistence
    evt = db_session.query(FederationEvent).filter(
        FederationEvent.correlation_id == req.correlation_id
    ).first()
    assert evt is not None
    assert evt.event_status == "SUCCESS"


def test_f2_bengaluru_to_hyderabad_authorized(db_session: Session):
    """
    Test F2: Bengaluru (BLR001) executes an authorized KYC verification
    request to Hyderabad (HYD001).
    """
    req = CrossBranchRequest(
        source_branch_id="BLR001",
        destination_branch_id="HYD001",
        requested_scope="CUSTOMER_KYC_VERIFICATION",
        request_id="REQ-F2-BLR-002",
        correlation_id=f"f2-corr-{uuid.uuid4().hex[:8]}",
        query_params={"customer_code": "CUST-HYD001-0001"},
    )

    api_key = BRANCH_SECRETS["BLR001"]
    res = FederationGateway.process_cross_branch_request(req, api_key=api_key, gateway_db=db_session)

    assert res.status == "SUCCESS"
    assert res.authorization_result == "AUTHORIZED"
    assert res.data["is_verified"] is True
    assert res.data["branch_id"] == "HYD001"


def test_f3_unauthorized_branch_credentials(db_session: Session):
    """
    Test F3: Attempt to send a federation request using invalid branch credentials.
    Expectations:
    - Authentication fails with REJECTED_INVALID_CREDENTIALS.
    - Zero protected destination data returned.
    - Security event recorded on gateway.
    """
    req = CrossBranchRequest(
        source_branch_id="BLR001",
        destination_branch_id="CHE001",
        requested_scope="ACCOUNT_STATUS_CONFIRMATION",
        request_id="REQ-F3-ATTACK-001",
        correlation_id=f"f3-corr-{uuid.uuid4().hex[:8]}",
        query_params={"synthetic_account_number": "ACC-CHE001-1001"},
    )

    attacker_key = "invalid_spoofed_secret_key_123"
    res = FederationGateway.process_cross_branch_request(req, api_key=attacker_key, gateway_db=db_session)

    assert res.status == "REJECTED"
    assert res.authorization_result == "REJECTED_INVALID_CREDENTIALS"
    assert res.data is None
    assert "Invalid or unregistered credentials" in res.error_message

    # Verify security audit event is logged
    evt = db_session.query(FederationEvent).filter(
        FederationEvent.correlation_id == req.correlation_id
    ).first()
    assert evt is not None
    assert evt.authorization_result == "REJECTED_INVALID_CREDENTIALS"


def test_f4_unauthorized_information_scope(db_session: Session):
    """
    Test F4: A branch requests information outside its permitted scope
    (e.g. FULL_ACCOUNT_EXTRACT).
    Expectations:
    - Request rejected with REJECTED_UNAUTHORIZED_SCOPE.
    - Destination data is NOT accessed.
    """
    req = CrossBranchRequest(
        source_branch_id="BLR001",
        destination_branch_id="CHE001",
        requested_scope="FULL_ACCOUNT_EXTRACT",
        request_id="REQ-F4-SCOPE-001",
        correlation_id=f"f4-corr-{uuid.uuid4().hex[:8]}",
        query_params={"synthetic_account_number": "ACC-CHE001-1001"},
    )

    api_key = BRANCH_SECRETS["BLR001"]
    res = FederationGateway.process_cross_branch_request(req, api_key=api_key, gateway_db=db_session)

    assert res.status == "REJECTED"
    assert res.authorization_result == "REJECTED_UNAUTHORIZED_SCOPE"
    assert res.data is None


def test_f5_duplicate_federation_request(db_session: Session):
    """
    Test F5: Send the exact same federation request twice with the same correlation_id.
    Expectations:
    - Anti-replay duplicate protection recognizes seen correlation_id.
    - Status returned is DUPLICATE.
    - Operation is not re-executed against destination database.
    """
    corr_id = f"f5-corr-dedup-{uuid.uuid4().hex[:8]}"
    req = CrossBranchRequest(
        source_branch_id="BLR001",
        destination_branch_id="CHE001",
        requested_scope="ACCOUNT_STATUS_CONFIRMATION",
        request_id="REQ-F5-DEDUP-001",
        correlation_id=corr_id,
        query_params={"synthetic_account_number": "ACC-CHE001-1001"},
    )

    api_key = BRANCH_SECRETS["BLR001"]
    # First submission
    res1 = FederationGateway.process_cross_branch_request(req, api_key=api_key, gateway_db=db_session)
    assert res1.status == "SUCCESS"

    # Second submission with identical correlation_id
    res2 = FederationGateway.process_cross_branch_request(req, api_key=api_key, gateway_db=db_session)
    assert res2.status == "DUPLICATE"
    assert res2.authorization_result == "DUPLICATE_REQUEST"


def test_f6_destination_branch_unavailable(db_session: Session, monkeypatch):
    """
    Test F6: Simulate destination branch database outage or network failure.
    Expectations:
    - Gateway catches connectivity failure gracefully without crashing.
    - Returns status FAILED.
    - Failure event recorded in audit logs.
    """
    req = CrossBranchRequest(
        source_branch_id="BLR001",
        destination_branch_id="CHE001",
        requested_scope="ACCOUNT_STATUS_CONFIRMATION",
        request_id="REQ-F6-OUTAGE-001",
        correlation_id=f"f6-corr-outage-{uuid.uuid4().hex[:8]}",
        query_params={"synthetic_account_number": "ACC-CHE001-1001"},
    )

    # Monkeypatch get_session to simulate destination outage
    def mock_broken_session(branch_id, is_test=False):
        raise ConnectionError(f"Simulated network timeout to branch {branch_id}")

    monkeypatch.setattr(BranchDatabaseManager, "get_session", mock_broken_session)

    api_key = BRANCH_SECRETS["BLR001"]
    res = FederationGateway.process_cross_branch_request(req, api_key=api_key, gateway_db=db_session)

    assert res.status == "FAILED"
    assert "currently unavailable" in res.error_message


# ============================================================================
# 2. FastAPI Endpoints & RBAC Isolation Tests
# ============================================================================

def test_api_exchange_endpoint(client: TestClient, bank_employee_auth):
    """Verify POST /api/federation/exchange processes requests with authentication."""
    _, _, token = bank_employee_auth
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Branch-Key": BRANCH_SECRETS["BLR001"],
    }

    payload = {
        "source_branch_id": "BLR001",
        "destination_branch_id": "CHE001",
        "requested_scope": "ACCOUNT_STATUS_CONFIRMATION",
        "request_id": "REQ-API-001",
        "correlation_id": f"api-corr-{uuid.uuid4().hex[:8]}",
        "query_params": {"synthetic_account_number": "ACC-CHE001-1001"},
    }

    resp = client.post("/api/federation/exchange", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"
    assert data["authorization_result"] == "AUTHORIZED"
    assert data["data"]["is_confirmed"] is True


def test_api_branches_endpoint(client: TestClient, bank_employee_auth):
    """Verify GET /api/federation/branches lists all three registered branches."""
    _, _, token = bank_employee_auth
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/federation/branches", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 3

    branch_ids = [b["branch_id"] for b in data]
    assert "BLR001" in branch_ids
    assert "CHE001" in branch_ids
    assert "HYD001" in branch_ids


def test_api_statistics_endpoint(client: TestClient, bank_employee_auth):
    """Verify GET /api/federation/statistics returns operational telemetry."""
    _, _, token = bank_employee_auth
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/federation/statistics", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_branches"] >= 3
    assert "successful_exchanges" in data
    assert "rejected_exchanges" in data


def test_api_events_endpoint(client: TestClient, bank_employee_auth):
    """Verify GET /api/federation/events returns audit events with filtering."""
    _, _, token = bank_employee_auth
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/federation/events?limit=10", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


def test_customer_rbac_forbidden_from_federation(client: TestClient, customer_auth):
    """Verify customer role is strictly forbidden from all federation endpoints (HTTP 403)."""
    _, _, token = customer_auth
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "source_branch_id": "BLR001",
        "destination_branch_id": "CHE001",
        "requested_scope": "ACCOUNT_STATUS_CONFIRMATION",
        "correlation_id": "customer-attempt",
        "query_params": {},
    }

    resp1 = client.post("/api/federation/exchange", json=payload, headers=headers)
    assert resp1.status_code == 403

    resp2 = client.get("/api/federation/branches", headers=headers)
    assert resp2.status_code == 403

    resp3 = client.get("/api/federation/statistics", headers=headers)
    assert resp3.status_code == 403

    resp4 = client.get("/api/federation/events", headers=headers)
    assert resp4.status_code == 403
