"""
BankFlow AI - Multi-Agent Simulation & State Machine Test Suite
Tests state machine transitions, concurrency distribution across RequestAgents,
scenario benchmarks 1-5, and bank simulation API endpoints.
"""

import sys
import os
from typing import Tuple
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.main import app
from app.database import get_db
from app.models.user import User, UserRole
from app.models.employee import Employee
from app.models.customer import Customer
from app.models.account import Account
from app.models.request import Request, ServiceType, RequestStatus
from app.models.audit_log import AuditLog
from app.auth.jwt_handler import create_access_token, clear_revoked_tokens
from app.auth.security import hash_password, login_rate_limiter
from app.simulation.state_machine import (
    transition_request,
    can_transition,
    InvalidStateTransitionError,
    DuplicateCompletionError,
)
from app.simulation.model import BankingSimulationModel
from app.simulation.configuration import SimulationConfig
from app.simulation.simulation_runner import simulation_runner


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
        username="sim_test_officer",
        email="sim_officer@bankflow.synthetic",
        password_hash=hash_password("BankAdmin@2026!"),
        role=UserRole.BANK_EMPLOYEE,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    emp = Employee(
        user_id=user.id,
        employee_code="EMP-SIM-001",
        full_name="Simulation Officer",
        department="Multi-Agent Operations",
        designation="Lead Supervisor",
        branch_id="BR-MAIN-001",
    )
    db_session.add(emp)
    db_session.flush()

    token = create_access_token(
        user_id=user.id,
        role=user.role.value,
        username=user.username,
    )
    return user, emp, token


# ----------------------------------------------------------------------------
# 1. STATE MACHINE TESTS
# ----------------------------------------------------------------------------

def test_state_machine_valid_progression(db_session: Session, sample_customer_and_account):
    """Test full valid lifecycle transition sequence and audit log entries."""
    customer, account = sample_customer_and_account

    req = Request(
        request_id="REQ-SM-01",
        customer_id=customer.id,
        account_id=account.id,
        service_type=ServiceType.CHEQUE_BOOK,
        request_status=RequestStatus.NEW,
    )
    db_session.add(req)
    db_session.flush()

    # NEW -> CLASSIFIED
    assert can_transition(RequestStatus.NEW, RequestStatus.CLASSIFIED) is True
    transition_request(db_session, req, RequestStatus.CLASSIFIED, "AGT-INTAKE-01")
    assert req.request_status == RequestStatus.CLASSIFIED

    # CLASSIFIED -> QUEUED
    assert can_transition(RequestStatus.CLASSIFIED, RequestStatus.QUEUED) is True
    transition_request(db_session, req, RequestStatus.QUEUED, "RequestAgent_1")
    assert req.request_status == RequestStatus.QUEUED

    # QUEUED -> VERIFIED
    assert can_transition(RequestStatus.QUEUED, RequestStatus.VERIFIED) is True
    transition_request(db_session, req, RequestStatus.VERIFIED, "AGT-VERIF-01")
    assert req.request_status == RequestStatus.VERIFIED

    # VERIFIED -> IN_SERVICE
    assert can_transition(RequestStatus.VERIFIED, RequestStatus.IN_SERVICE) is True
    transition_request(db_session, req, RequestStatus.IN_SERVICE, "ServiceAgent_CHEQUE_BOOK")
    assert req.request_status == RequestStatus.IN_SERVICE

    # IN_SERVICE -> COMPLETED
    assert can_transition(RequestStatus.IN_SERVICE, RequestStatus.COMPLETED) is True
    transition_request(db_session, req, RequestStatus.COMPLETED, "ServiceAgent_CHEQUE_BOOK")
    assert req.request_status == RequestStatus.COMPLETED
    assert req.completed_at is not None

    # Check audit log trail
    logs = db_session.query(AuditLog).filter(AuditLog.entity_id == "REQ-SM-01").all()
    assert len(logs) == 5


def test_state_machine_invalid_transition_raises_error(db_session: Session, sample_customer_and_account):
    """Test illegal state transitions raise InvalidStateTransitionError."""
    customer, account = sample_customer_and_account

    req = Request(
        request_id="REQ-SM-02",
        customer_id=customer.id,
        account_id=account.id,
        service_type=ServiceType.CHEQUE_BOOK,
        request_status=RequestStatus.NEW,
    )
    db_session.add(req)
    db_session.flush()

    # NEW directly to COMPLETED is prohibited
    assert can_transition(RequestStatus.NEW, RequestStatus.COMPLETED) is False
    with pytest.raises(InvalidStateTransitionError):
        transition_request(db_session, req, RequestStatus.COMPLETED, "AGT-TEST")


def test_state_machine_duplicate_completion_raises_error(db_session: Session, sample_customer_and_account):
    """Test transitioning an already COMPLETED request raises DuplicateCompletionError."""
    customer, account = sample_customer_and_account

    req = Request(
        request_id="REQ-SM-03",
        customer_id=customer.id,
        account_id=account.id,
        service_type=ServiceType.CHEQUE_BOOK,
        request_status=RequestStatus.COMPLETED,
    )
    db_session.add(req)
    db_session.flush()

    with pytest.raises(DuplicateCompletionError):
        transition_request(db_session, req, RequestStatus.IN_SERVICE, "AGT-TEST")


# ----------------------------------------------------------------------------
# 2. CONCURRENCY & WORKER POOL TESTS
# ----------------------------------------------------------------------------

def test_concurrent_dispatch_across_request_agents(db_session: Session, sample_customer_and_account):
    """Test that multiple classified requests are assigned concurrently to available RequestAgents."""
    customer, account = sample_customer_and_account
    model = BankingSimulationModel(SimulationConfig(num_request_agents=3))

    # Create 3 classified requests
    reqs = []
    for i in range(1, 4):
        req = Request(
            request_id=f"REQ-CONCUR-{i}",
            customer_id=customer.id,
            account_id=account.id,
            service_type=ServiceType.CHEQUE_BOOK,
            request_status=RequestStatus.CLASSIFIED,
            payload={"account_id": account.id, "number_of_leaves": 25},
        )
        db_session.add(req)
        reqs.append(req)
    db_session.flush()

    # Step the model tick
    res = model.step(db_session)

    # All 3 requests should have been dispatched to RequestAgent_1, RequestAgent_2, RequestAgent_3
    assert res["dispatched_to_request_agents"] == 3
    request_agents = model.get_request_agents()
    assert len(request_agents) == 3

    # Verify each agent holds a distinct request
    assigned_requests = {agent.current_request_id for agent in request_agents}
    assert assigned_requests == {"REQ-CONCUR-1", "REQ-CONCUR-2", "REQ-CONCUR-3"}
    assert all(not agent.is_available for agent in request_agents)


# ----------------------------------------------------------------------------
# 3. SCENARIOS TESTS (Benchmarks 1, 3, 5)
# ----------------------------------------------------------------------------

def test_scenario_1_normal_processing(db_session: Session):
    """Test Scenario 1: Normal Processing (20 valid requests, 3 Request Agents)."""
    result = simulation_runner.run_scenario(1, db_session)

    assert result["scenario_id"] == 1
    assert result["total_requests"] == 20
    assert result["request_agents_count"] == 3
    assert result["peak_concurrency"] >= 2
    assert "COMPLETED" in result["status_breakdown"]
    assert result["status_breakdown"]["COMPLETED"] > 0


def test_scenario_3_incomplete_requests(db_session: Session):
    """Test Scenario 3: Incomplete Requests (triggers NEEDS_CORRECTION)."""
    result = simulation_runner.run_scenario(3, db_session)

    assert result["scenario_id"] == 3
    assert result["total_requests"] == 20
    assert "NEEDS_CORRECTION" in result["status_breakdown"]
    assert result["status_breakdown"]["NEEDS_CORRECTION"] > 0


def test_scenario_5_human_review_referrals(db_session: Session):
    """Test Scenario 5: Human Review Gate (account applications & security referrals)."""
    result = simulation_runner.run_scenario(5, db_session)

    assert result["scenario_id"] == 5
    assert result["total_requests"] == 20
    assert "HUMAN_REVIEW" in result["status_breakdown"]
    assert result["status_breakdown"]["HUMAN_REVIEW"] > 0


# ----------------------------------------------------------------------------
# 4. SIMULATION REST API ENDPOINTS
# ----------------------------------------------------------------------------

def test_bank_agents_list_endpoint(client: TestClient, bank_employee_auth):
    """Test GET /api/bank/agents returns registered simulation agents."""
    _, _, token = bank_employee_auth
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/bank/agents", headers=headers)
    assert resp.status_code == 200
    agents_data = resp.json()
    assert "agents" in agents_data
    assert "total" in agents_data
    agents = agents_data["agents"]
    assert isinstance(agents, list)
    assert len(agents) >= 9

    codes = [a["agent_code"] for a in agents]
    assert "AGT-INTAKE-01" in codes
    assert "AGT-VERIF-01" in codes
    assert "RequestAgent_1" in codes
    assert "AGT-SUPERVISOR-01" in codes


def test_bank_agents_statistics_endpoint(client: TestClient, bank_employee_auth):
    """Test GET /api/bank/agents/statistics returns aggregated metrics."""
    _, _, token = bank_employee_auth
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/bank/agents/statistics", headers=headers)
    assert resp.status_code == 200
    stats = resp.json()
    assert "total_agents" in stats
    assert "available_agents" in stats
    assert "busy_agents" in stats
    assert "total_requests_processed" in stats


def test_bank_simulation_status_endpoint(client: TestClient, bank_employee_auth):
    """Test GET /api/bank/simulation/status returns current simulation state."""
    _, _, token = bank_employee_auth
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/bank/simulation/status", headers=headers)
    assert resp.status_code == 200
    status_data = resp.json()
    assert "is_running" in status_data
    assert "current_tick" in status_data
    assert "active_workers" in status_data


def test_bank_simulation_run_scenario_endpoint(client: TestClient, bank_employee_auth):
    """Test POST /api/bank/simulation/run-test triggers scenario benchmark and returns results."""
    _, _, token = bank_employee_auth
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"scenario_id": 1}
    resp = client.post("/api/bank/simulation/run-test", json=payload, headers=headers)
    assert resp.status_code == 200
    res = resp.json()
    assert res["scenario_id"] == 1
    assert "peak_concurrency" in res
    assert "status_breakdown" in res
    assert len(res["execution_logs"]) > 0


def test_customer_forbidden_from_simulation_apis(client: TestClient, sample_customer_and_account):
    """Test CUSTOMER role is forbidden (403) from bank simulation control endpoints."""
    customer, _ = sample_customer_and_account
    token = create_access_token(
        user_id=customer.user_id,
        role="CUSTOMER",
        username=customer.user.username,
    )
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/bank/agents", headers=headers)
    assert resp.status_code == 403

    resp = client.post("/api/bank/simulation/run-test", json={"scenario_id": 1}, headers=headers)
    assert resp.status_code == 403
