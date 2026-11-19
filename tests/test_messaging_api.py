"""
BankFlow AI - Messaging REST API & RBAC Test Suite
Tests broker status, queue monitoring, event history, dead-letter endpoints,
and role-based access control.
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
from app.models.agent_event import AgentEvent
from app.models.processed_message import ProcessedMessage
from app.auth.jwt_handler import create_access_token, clear_revoked_tokens
from app.auth.security import hash_password, login_rate_limiter
from app.messaging.queues import declare_queues_and_bindings


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
        username="msg_test_officer",
        email="msg_officer@bankflow.synthetic",
        password_hash=hash_password("BankAdmin@2026!"),
        role=UserRole.BANK_EMPLOYEE,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    emp = Employee(
        user_id=user.id,
        employee_code="EMP-MSG-001",
        full_name="Messaging Officer",
        department="Operations",
        designation="Lead Analyst",
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


def test_get_broker_status_endpoint(client: TestClient, bank_employee_auth):
    """Test GET /api/bank/messaging/status returns broker health."""
    _, _, token = bank_employee_auth
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/bank/messaging/status", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "broker_status" in data
    assert "connected" in data
    assert data["connected"] is True
    assert data["main_exchange"] == "bankflow.events"
    assert data["dlx_exchange"] == "bankflow.dlx"


def test_get_queues_status_endpoint(client: TestClient, bank_employee_auth):
    """Test GET /api/bank/messaging/queues returns queue depths."""
    _, _, token = bank_employee_auth
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/bank/messaging/queues", headers=headers)
    assert resp.status_code == 200
    queues = resp.json()
    assert isinstance(queues, list)
    assert len(queues) >= 7

    names = [q["queue_name"] for q in queues]
    assert "bankflow.intake.q" in names
    assert "bankflow.dlq" in names


def test_get_communication_statistics_endpoint(client: TestClient, bank_employee_auth):
    """Test GET /api/bank/messaging/statistics returns aggregate broker metrics."""
    _, _, token = bank_employee_auth
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/bank/messaging/statistics", headers=headers)
    assert resp.status_code == 200
    stats = resp.json()
    assert "total_messages_published" in stats
    assert "total_messages_consumed" in stats
    assert "successfully_processed" in stats
    assert "duplicate_messages_caught" in stats


def test_get_events_history_and_timeline_endpoints(client: TestClient, db_session: Session, bank_employee_auth):
    """Test GET /api/bank/messaging/events and GET /api/bank/messaging/events/{request_id}."""
    _, _, token = bank_employee_auth
    headers = {"Authorization": f"Bearer {token}"}

    # Seed an agent event
    evt = AgentEvent(
        event_id="EVT-API-TEST-001",
        request_id="REQ-API-9901",
        agent_id="AGT-INTAKE-01",
        event_type="REQUEST_CLASSIFIED",
        previous_state="NEW",
        new_state="CLASSIFIED",
    )
    db_session.add(evt)
    db_session.flush()

    # 1. Paginated list
    resp = client.get("/api/bank/messaging/events?request_id=REQ-API-9901", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert data["items"][0]["event_id"] == "EVT-API-TEST-001"

    # 2. Request timeline
    resp_timeline = client.get("/api/bank/messaging/events/REQ-API-9901", headers=headers)
    assert resp_timeline.status_code == 200
    timeline = resp_timeline.json()
    assert len(timeline) >= 1
    assert timeline[0]["request_id"] == "REQ-API-9901"


def test_dead_letter_list_and_retry_endpoint(client: TestClient, db_session: Session, bank_employee_auth):
    """Test GET /api/bank/messaging/dead-letter and POST /api/bank/messaging/retry/{message_id}."""
    declare_queues_and_bindings()
    _, _, token = bank_employee_auth
    headers = {"Authorization": f"Bearer {token}"}

    # Seed a dead-letter record
    msg_id = "DL-TEST-MESSAGE-UUID"
    dl_record = ProcessedMessage(
        message_id=msg_id,
        request_id="REQ-DEAD-TEST-01",
        event_type="REQUEST_CLASSIFIED",
        consumer_name="RequestAgent_1",
        processing_status="DEAD_LETTER",
        retry_count=3,
        error_message="Simulated permanent partition",
    )
    db_session.add(dl_record)
    db_session.flush()

    # 1. Check dead letter listing
    resp_list = client.get("/api/bank/messaging/dead-letter", headers=headers)
    assert resp_list.status_code == 200
    data = resp_list.json()
    msg_ids = [item["message_id"] for item in data["items"]]
    assert msg_id in msg_ids

    # 2. Retry dead letter
    resp_retry = client.post(f"/api/bank/messaging/retry/{msg_id}", headers=headers)
    assert resp_retry.status_code == 200
    retry_data = resp_retry.json()
    assert retry_data["status"] == "RE_QUEUED"
    assert retry_data["message_id"] == msg_id


def test_agent_communication_metrics_endpoint(client: TestClient, bank_employee_auth):
    """Test GET /api/bank/agents/communication returns per-agent metrics."""
    _, _, token = bank_employee_auth
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/bank/agents/communication", headers=headers)
    assert resp.status_code == 200
    metrics = resp.json()
    assert isinstance(metrics, list)
    assert len(metrics) >= 9


def test_customer_forbidden_from_messaging_endpoints(client: TestClient, sample_customer_and_account):
    """Verify customer role cannot access internal broker management endpoints."""
    customer, _ = sample_customer_and_account
    token = create_access_token(
        user_id=customer.user_id,
        role="CUSTOMER",
        username=customer.user.username,
    )
    headers = {"Authorization": f"Bearer {token}"}

    # Forbidden 403
    resp1 = client.get("/api/bank/messaging/status", headers=headers)
    assert resp1.status_code == 403

    resp2 = client.get("/api/bank/messaging/queues", headers=headers)
    assert resp2.status_code == 403

    resp3 = client.post("/api/bank/messaging/retry/fake-id", headers=headers)
    assert resp3.status_code == 403
