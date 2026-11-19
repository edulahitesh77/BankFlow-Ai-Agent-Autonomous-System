"""
BankFlow AI - Real-Time Agent Monitoring Tests
Validates real-time multi-agent telemetry, WebSocket / REST synchronization,
role-based access control, concurrent request processing, and live event log streaming.
"""

import sys
import os
import pytest
from starlette.testclient import TestClient

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.main import app
from app.database import get_db
from app.models.user import User, UserRole
from app.models.employee import Employee
from app.models.customer import Customer
from app.models.account import Account
from app.models.request import Request, RequestStatus, ServiceType
from app.auth.jwt_handler import create_access_token, clear_revoked_tokens
from app.auth.security import hash_password, login_rate_limiter
from app.simulation.simulation_runner import simulation_runner
from app.simulation.configuration import SimulationConfig
from app.simulation.model import BankingSimulationModel


@pytest.fixture
def api_client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    login_rate_limiter.reset_all()
    clear_revoked_tokens()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def employee_token(db_session):
    user = User(
        username="rt_monitor_officer",
        email="rt_officer@bankflow.test",
        password_hash=hash_password("Monitor@2026!"),
        role=UserRole.BANK_EMPLOYEE,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    emp = Employee(
        user_id=user.id,
        employee_code="EMP-RT-01",
        full_name="Monitoring Test Officer",
        department="Operations",
        designation="Operations Officer",
        branch_id="BLR001",
    )
    db_session.add(emp)
    db_session.commit()

    return create_access_token(
        role="BANK_EMPLOYEE",
        username=user.username,
        user_id=user.id,
    )


@pytest.fixture
def customer_token(db_session):
    user = User(
        username="rt_cust_user",
        email="rt_cust@bankflow.test",
        password_hash=hash_password("Customer@2026!"),
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    return create_access_token(
        role="CUSTOMER",
        username=user.username,
        user_id=user.id,
    )


def test_realtime_monitoring_rbac_unauthenticated(api_client):
    """Verifies unauthenticated access to real-time agent monitoring is rejected with 401."""
    resp = api_client.get("/api/bank/agents/realtime-monitoring")
    assert resp.status_code == 401


def test_realtime_monitoring_rbac_customer_forbidden(api_client, customer_token):
    """Verifies that customers cannot access internal bank employee agent monitoring."""
    resp = api_client.get(
        "/api/bank/agents/realtime-monitoring",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert resp.status_code == 403


def test_realtime_monitoring_endpoint_employee_authorized(api_client, employee_token, db_session):
    """Verifies bank employees can access complete real-time monitoring telemetry."""
    resp = api_client.get(
        "/api/bank/agents/realtime-monitoring",
        headers={"Authorization": f"Bearer {employee_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert "is_running" in data
    assert "status_indicator" in data
    assert data["status_indicator"] in ("LIVE", "SIMULATION STOPPED")
    assert "metrics" in data
    assert "agents" in data
    assert "events" in data

    # Verify metrics fields
    metrics = data["metrics"]
    assert "total_requests" in metrics
    assert "processed_requests" in metrics
    assert "failed_requests" in metrics
    assert "pending_requests" in metrics
    assert "active_workers" in metrics
    assert "total_agents" in metrics

    # Verify all agent categories are present
    agents = data["agents"]
    assert len(agents) >= 6

    agent_types = {a["agent_type"] for a in agents}
    assert "CUSTOMER" in agent_types
    assert "INTAKE" in agent_types
    assert "VERIFICATION" in agent_types
    assert "REQUEST" in agent_types
    assert "SERVICE" in agent_types
    assert "SUPERVISOR" in agent_types

    # Verify agent fields: actual ID, code, status, stage, current_request_id
    for agt in agents:
        assert agt["agent_code"]
        assert agt["status"] in ("IDLE", "BUSY", "PROCESSING", "FAILED", "RECOVERING")
        assert "current_stage" in agt
        assert "completed_tasks" in agt
        assert "supported_skills" in agt


def test_concurrent_request_processing_by_multiple_request_agents(db_session, api_client, employee_token):
    """
    Submits multiple concurrent requests and steps the multi-agent system,
    demonstrating that distinct Request Agents process work concurrently.
    """
    # 1. Ensure test customer and account exist
    cust = db_session.query(Customer).first()
    if not cust:
        u = User(username="cust_rt_demo", email="demo@test.com", password_hash=hash_password("Test@123"), role=UserRole.CUSTOMER)
        db_session.add(u)
        db_session.flush()
        cust = Customer(user_id=u.id, customer_code="CUST-RT-DEMO", full_name="Demo Customer", email=u.email, phone="123456", branch_id="BLR001")
        db_session.add(cust)
        db_session.flush()

    acc = db_session.query(Account).filter(Account.customer_id == cust.id).first()
    if not acc:
        acc = Account(customer_id=cust.id, synthetic_account_number="ACC-RT-DEMO-01", account_type="SAVINGS", account_status="ACTIVE", branch_id="BLR001")
        db_session.add(acc)
        db_session.flush()

    # 2. Seed 3 concurrent requests into PostgreSQL with NEW status
    req_codes = [f"BFA-CONC-TEST-{i}" for i in range(1, 4)]
    for code in req_codes:
        existing = db_session.query(Request).filter(Request.request_id == code).first()
        if existing:
            db_session.delete(existing)
            db_session.flush()

        req = Request(
            request_id=code,
            customer_id=cust.id,
            account_id=acc.id,
            service_type=ServiceType.CHEQUE_BOOK,
            request_status=RequestStatus.NEW,
            priority="HIGH",
            payload={"number_of_leaves": 50, "account_number": acc.synthetic_account_number},
            branch_id="BLR001",
            origin_branch_id="BLR001",
        )
        db_session.add(req)
    db_session.commit()

    # 3. Initialize model with at least 4 Request Agents and step Phase 1 (Intake) and Phase 2 (Dispatch)
    model = BankingSimulationModel(SimulationConfig(num_request_agents=4, tick_delay_seconds=0.0))
    simulation_runner.model = model

    # Tick 1: Intake processes NEW requests -> CLASSIFIED
    model.step(db_session)

    # Tick 2: Scheduler dispatches CLASSIFIED requests to available Request Agents
    model.step(db_session)

    # 4. Verify that multiple distinct Request Agents received concurrent assignments
    active_workers = [w for w in model.request_agent_pool if w.current_request_id is not None]
    assigned_worker_codes = [w.agent_code for w in active_workers]
    assigned_request_ids = [w.current_request_id for w in active_workers]

    # Verify concurrency: Multiple workers assigned
    assert len(active_workers) >= 2
    # Verify unique workers assigned: Each request has a distinct worker
    assert len(set(assigned_worker_codes)) == len(assigned_worker_codes)

    # 5. Verify real-time monitoring reflects this actual concurrent backend assignment
    resp = api_client.get(
        "/api/bank/agents/realtime-monitoring",
        headers={"Authorization": f"Bearer {employee_token}"},
    )
    assert resp.status_code == 200
    telemetry = resp.json()

    # Check active workers in telemetry matches
    busy_req_agents = [
        a for a in telemetry["agents"]
        if a["agent_type"] == "REQUEST" and a["current_request_id"] is not None
    ]
    assert len(busy_req_agents) >= 2
    for b_agent in busy_req_agents:
        assert b_agent["status"] in ("PROCESSING", "BUSY")
        assert b_agent["current_request_id"] in req_codes


def test_websocket_monitoring_authentication_and_streaming(api_client, employee_token, customer_token):
    """Verifies WebSocket endpoint authentication and streaming telemetry."""
    # 1. Unauthenticated or Customer token is rejected with WS 1008
    with pytest.raises(Exception):
        with api_client.websocket_connect("/ws/agents/monitoring") as ws:
            ws.receive_json()

    with pytest.raises(Exception):
        with api_client.websocket_connect(f"/ws/agents/monitoring?token={customer_token}") as ws:
            ws.receive_json()

    # 2. Valid Employee token successfully receives live JSON telemetry
    with api_client.websocket_connect(f"/ws/agents/monitoring?token={employee_token}") as ws:
        data = ws.receive_json()
        assert "status_indicator" in data
        assert "metrics" in data
        assert "agents" in data
        assert "events" in data
        assert len(data["agents"]) >= 6
