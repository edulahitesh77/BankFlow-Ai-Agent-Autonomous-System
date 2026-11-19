"""
BankFlow AI - AI Workflow Visualizer Endpoint Tests
Tests RBAC authentication, topology endpoints, request journey reconstruction,
rule-based decision audits, and real-time performance analytics.
"""

import pytest
import uuid
from starlette.testclient import TestClient
from app.main import app
from app.database import get_db
from app.models.user import User, UserRole
from app.models.employee import Employee
from app.models.customer import Customer
from app.models.request import Request, RequestStatus, ServiceType
from app.models.agent_event import AgentEvent
from app.auth.jwt_handler import create_access_token, clear_revoked_tokens
from app.auth.security import hash_password, login_rate_limiter


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
        username="vis_officer_test",
        email="vis_officer@bankflow.test",
        password_hash=hash_password("Monitor@2026!"),
        role=UserRole.BANK_EMPLOYEE,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    emp = Employee(
        user_id=user.id,
        employee_code="EMP-VIS-01",
        full_name="Visualizer Test Officer",
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
        username="vis_cust_user",
        email="vis_cust@bankflow.test",
        password_hash=hash_password("Customer@2026!"),
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    cust = Customer(
        user_id=user.id,
        customer_code="CUST-VIS-01",
        full_name="Visualizer Test Customer",
        email=user.email,
        branch_id="BLR001",
    )
    db_session.add(cust)
    db_session.commit()

    return create_access_token(
        role="CUSTOMER",
        username=user.username,
        user_id=user.id,
    )


def test_visualizer_endpoints_rbac_unauthenticated(api_client):
    """Verifies that visualizer endpoints reject unauthenticated access with 401."""
    assert api_client.get("/api/bank/visualizer/recent-requests").status_code == 401
    assert api_client.get("/api/bank/visualizer/decisions").status_code == 401
    assert api_client.get("/api/bank/visualizer/analytics").status_code == 401
    assert api_client.get("/api/bank/visualizer/request-journey/REQ-NONEXISTENT").status_code == 401


def test_visualizer_endpoints_rbac_customer_forbidden(api_client, customer_token):
    """Verifies that customer tokens are forbidden (403) from accessing employee visualizer endpoints."""
    headers = {"Authorization": f"Bearer {customer_token}"}
    assert api_client.get("/api/bank/visualizer/recent-requests", headers=headers).status_code == 403
    assert api_client.get("/api/bank/visualizer/decisions", headers=headers).status_code == 403
    assert api_client.get("/api/bank/visualizer/analytics", headers=headers).status_code == 403


def test_visualizer_recent_requests_and_journey(api_client, employee_token, customer_token, db_session):
    """Verifies recent requests listing and end-to-end journey reconstruction."""
    headers = {"Authorization": f"Bearer {employee_token}"}

    # Fetch customer seeded by customer_token fixture
    cust = db_session.query(Customer).filter(Customer.customer_code == "CUST-VIS-01").first()
    test_req_id = f"REQ-VIS-{uuid.uuid4().hex[:6]}"

    # Seed test request
    req = Request(
        request_id=test_req_id,
        customer_id=cust.id,
        service_type=ServiceType.CHEQUE_BOOK,
        request_status=RequestStatus.COMPLETED,
        priority="HIGH",
        reason_code="AUTOMATED_TEST_RUN",
    )
    db_session.add(req)
    db_session.commit()

    # Seed agent events
    ev1 = AgentEvent(
        event_id=f"EV-VIS-1-{uuid.uuid4().hex[:6]}",
        request_id=test_req_id,
        agent_id="AGT-INTAKE-01",
        event_type="REQUEST_CLASSIFIED",
        previous_state="NEW",
        new_state="CLASSIFIED",
        reason_code="INTAKE_CLASSIFICATION_PASSED",
    )
    ev2 = AgentEvent(
        event_id=f"EV-VIS-2-{uuid.uuid4().hex[:6]}",
        request_id=test_req_id,
        agent_id="RequestAgent_0",
        event_type="REQUEST_ASSIGNED",
        previous_state="CLASSIFIED",
        new_state="QUEUED",
        reason_code="LEAST_LOADED_POLICY",
    )
    ev3 = AgentEvent(
        event_id=f"EV-VIS-3-{uuid.uuid4().hex[:6]}",
        request_id=test_req_id,
        agent_id="AGT-VERIF-01",
        event_type="VERIFICATION_COMPLETED",
        previous_state="QUEUED",
        new_state="VERIFIED",
        reason_code="IDENTITY_VERIFIED_AUTHENTIC",
    )
    db_session.add_all([ev1, ev2, ev3])
    db_session.commit()

    # Test recent-requests
    resp = api_client.get("/api/bank/visualizer/recent-requests", headers=headers)
    assert resp.status_code == 200
    requests_list = resp.json()
    assert any(r["request_id"] == test_req_id for r in requests_list)

    # Test request-journey
    resp_journey = api_client.get(f"/api/bank/visualizer/request-journey/{test_req_id}", headers=headers)
    assert resp_journey.status_code == 200
    journey = resp_journey.json()
    assert journey["request_id"] == test_req_id
    assert journey["step_count"] >= 4
    assert any(s["agent_id"] == "AGT-INTAKE-01" for s in journey["steps"])
    assert any(s["agent_id"] == "RequestAgent_0" for s in journey["steps"])
    assert any(s["agent_id"] == "AGT-VERIF-01" for s in journey["steps"])


def test_visualizer_decisions_and_analytics(api_client, employee_token):
    """Verifies rule-based decision logs and performance analytics endpoints."""
    headers = {"Authorization": f"Bearer {employee_token}"}

    # Test decisions
    resp_dec = api_client.get("/api/bank/visualizer/decisions?limit=10", headers=headers)
    assert resp_dec.status_code == 200
    decisions = resp_dec.json()
    assert isinstance(decisions, list)
    if decisions:
        first = decisions[0]
        assert "decision_id" in first
        assert "agent_id" in first
        assert "decision_type" in first
        assert first["engine_type"] == "DETERMINISTIC_RULE_BASED"

    # Test analytics
    resp_an = api_client.get("/api/bank/visualizer/analytics", headers=headers)
    assert resp_an.status_code == 200
    analytics = resp_an.json()
    assert "overview" in analytics
    assert "status_distribution" in analytics
    assert "agent_utilization" in analytics
    assert "event_volume" in analytics
    assert analytics["overview"]["total_requests"] >= 0
