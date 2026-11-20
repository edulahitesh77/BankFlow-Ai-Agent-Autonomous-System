"""
BankFlow AI - Visualizer Upgrades Tests
Tests federation topology, cross-branch exchange simulation, security overview,
all 7 controlled security attack/defense scenarios, and supervisor failure recovery.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import get_db
from app.models.user import User, UserRole
from app.auth.security import hash_password
from app.auth.jwt_handler import create_access_token


@pytest.fixture(scope="function")
def client(db_session: Session) -> TestClient:
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def bank_employee_token(db_session: Session) -> str:
    """Creates a bank employee and generates valid access token."""
    user = db_session.query(User).filter_by(username="vis_test_employee").first()
    if not user:
        user = User(
            username="vis_test_employee",
            email="vis_emp@bankflow.synthetic",
            password_hash=hash_password("Employee@2026!"),
            role=UserRole.BANK_EMPLOYEE,
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

    return create_access_token(user_id=user.id, role=user.role.value, username=user.username)


def test_federation_topology_endpoint(client: TestClient, bank_employee_token: str):
    """Test retrieving federation network topology."""
    resp = client.get(
        "/api/bank/visualizer/federation/topology",
        headers={"Authorization": f"Bearer {bank_employee_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "gateway" in data
    assert data["gateway"]["id"] == "FED-GATEWAY-CORE"
    assert "branches" in data
    assert len(data["branches"]) >= 3
    branch_ids = [b["branch_id"] for b in data["branches"]]
    assert "BLR001" in branch_ids
    assert "CHE001" in branch_ids
    assert "HYD001" in branch_ids


def test_simulate_federation_exchange_authorized(client: TestClient, bank_employee_token: str):
    """Test simulating an authorized cross-branch query from BLR to CHE."""
    payload = {
        "source_branch_id": "BLR001",
        "destination_branch_id": "CHE001",
        "requested_scope": "ACCOUNT_STATUS_CONFIRMATION",
        "auth_mode": "VALID",
    }
    resp = client.post(
        "/api/bank/visualizer/federation/simulate-exchange",
        json=payload,
        headers={"Authorization": f"Bearer {bank_employee_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_success"] is True
    assert "trajectory_steps" in data
    assert len(data["trajectory_steps"]) >= 4
    stages = [s["stage"] for s in data["trajectory_steps"]]
    assert "SOURCE_DISPATCH" in stages
    assert "GATEWAY_HMAC_AUTHENTICATION" in stages
    assert "GATEWAY_SCOPE_AUTHORIZATION" in stages


def test_simulate_federation_exchange_unauthorized_key(client: TestClient, bank_employee_token: str):
    """Test simulating an unauthorized branch with forged secret."""
    payload = {
        "source_branch_id": "BLR001",
        "destination_branch_id": "CHE001",
        "requested_scope": "ACCOUNT_STATUS_CONFIRMATION",
        "auth_mode": "INVALID_KEY",
    }
    resp = client.post(
        "/api/bank/visualizer/federation/simulate-exchange",
        json=payload,
        headers={"Authorization": f"Bearer {bank_employee_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_success"] is False
    assert data["result"]["status"] == "REJECTED"
    stages = [s["stage"] for s in data["trajectory_steps"]]
    assert "ACCESS_DENIED_HALTED" in stages


def test_security_overview_endpoint(client: TestClient, bank_employee_token: str):
    """Test security overview parameters (Argon2id, JWT, AES-256-GCM, TLS, RBAC)."""
    resp = client.get(
        "/api/bank/visualizer/security/overview",
        headers={"Authorization": f"Bearer {bank_employee_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["argon2id"]["status"] == "ENFORCED"
    assert data["argon2id"]["reversible"] is False
    assert data["aes_gcm"]["status"] == "ENFORCED"
    assert data["aes_gcm"]["reversible"] is True
    assert data["jwt"]["status"] == "ENFORCED"
    assert data["rbac"]["status"] == "ENFORCED"
    assert "recent_audit_logs" in data


@pytest.mark.parametrize("scenario_id", [
    "SCENARIO_1_VALID_LOGIN",
    "SCENARIO_2_INVALID_LOGIN",
    "SCENARIO_3_CUSTOMER_ACCESS_EMPLOYEE",
    "SCENARIO_4_UNAUTHORIZED_BRANCH",
    "SCENARIO_5_EXPIRED_JWT",
    "SCENARIO_6_DUPLICATE_FEDERATION",
    "SCENARIO_7_OUTSIDE_SCOPE",
])
def test_all_seven_security_scenarios(client: TestClient, bank_employee_token: str, scenario_id: str):
    """Test all 7 controlled attack/defense simulation scenarios."""
    resp = client.post(
        "/api/bank/visualizer/security/execute-scenario",
        json={"scenario_id": scenario_id},
        headers={"Authorization": f"Bearer {bank_employee_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["scenario_id"] == scenario_id
    assert "checks" in data
    assert len(data["checks"]) >= 3
    assert "reason_code" in data
    assert "audit_id" in data


def test_simulate_recovery_sequence(client: TestClient, bank_employee_token: str):
    """Test supervisor failure detection and request reassignment sequence."""
    resp = client.post(
        "/api/bank/visualizer/recovery/simulate-recovery",
        json={"failed_agent_code": "AGT-REQ-01"},
        headers={"Authorization": f"Bearer {bank_employee_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["failed_agent"] == "AGT-REQ-01"
    assert data["backup_worker"] == "AGT-REQ-02"
    assert len(data["steps"]) == 8
    stages = [s["stage"] for s in data["steps"]]
    assert "AGENT_FAILURE" in stages
    assert "SUPERVISOR_DETECTION" in stages
    assert "ATOMIC_REASSIGNMENT" in stages
    assert "COMPLETION_CONFIRMED" in stages
