"""
BankFlow AI - Unity 2D Export & Visualization Test Suite (Phase 9)
Tests simulation manifest schemas, atomic file writing, benchmark replay generation,
authoritative metric computations, stage mappings, and FastAPI export endpoints.
"""

import sys
import os
import json
import pytest
from typing import Tuple
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
from app.models.agent import Agent as DBAgent, AgentType, AgentHealthStatus
from app.auth.jwt_handler import create_access_token, clear_revoked_tokens
from app.auth.security import hash_password, login_rate_limiter
from app.schemas.unity_export import (
    RequestExportItem,
    AgentExportItem,
    SimulationEventExportItem,
    SimulationSnapshotExport,
    SimulationMetricsExport,
    SimulationManifestExport,
)
from app.simulation.exporter import SimulationExporter, atomic_write_json, STAGE_MAPPING


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
        username="unity_test_officer",
        email="unity_officer@bankflow.test",
        password_hash=hash_password("UnitySecure@2026!"),
        role=UserRole.BANK_EMPLOYEE,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    emp = Employee(
        user_id=user.id,
        employee_code="EMP-TEST-UNITY-01",
        full_name="Unity Visual Test Officer",
        department="Multi-Agent Systems",
        designation="Simulation Analyst",
        branch_id="BR-MAIN-001",
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
        username="unity_test_customer",
        email="unity_cust@bankflow.test",
        password_hash=hash_password("CustSecure@2026!"),
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    cust = Customer(
        user_id=user.id,
        customer_code="CUST-UNITY-01",
        full_name="Unity Test Customer",
        email=user.email,
        phone="+1-555-0999",
        branch_id="BR-MAIN-001",
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
# 1. Pydantic Schemas & Data Structure Tests
# ============================================================================

def test_simulation_manifest_schema():
    """Verify that SimulationManifestExport strictly enforces schema requirements."""
    metrics = SimulationMetricsExport(
        total_requests=10,
        completed_requests=8,
        failed_requests=1,
        pending_requests=1,
        human_review_requests=0,
        recovered_requests=1,
        avg_waiting_time_ticks=1.5,
        avg_completion_time_ticks=3.8,
        throughput_per_minute=24.0,
        request_agent_utilization=0.67,
        message_integrity_rate=100.0,
    )

    snapshot = SimulationSnapshotExport(
        tick=0,
        timestamp="2026-11-19T00:00:00Z",
        queue_counts={"NEW": 10},
        active_requests=[],
        agents=[],
    )

    manifest = SimulationManifestExport(
        schema_version="1.0.0",
        simulation_id="SIM-TEST-001",
        scenario_name="Test Scenario",
        exported_at="2026-11-19T00:00:00Z",
        total_ticks=1,
        total_events=0,
        metrics=metrics,
        snapshots=[snapshot],
        events=[],
    )

    data = manifest.model_dump()
    assert data["schema_version"] == "1.0.0"
    assert data["simulation_id"] == "SIM-TEST-001"
    assert data["metrics"]["message_integrity_rate"] == 100.0
    assert len(data["snapshots"]) == 1


def test_stage_mappings():
    """Verify mapping of all backend RequestStatus enums to 8 visual workflow stages."""
    assert SimulationExporter.map_request_stage("NEW") == "STAGE_1_CUSTOMER"
    assert SimulationExporter.map_request_stage("CLASSIFIED") == "STAGE_2_INTAKE"
    assert SimulationExporter.map_request_stage("QUEUED") == "STAGE_3_ASSIGNMENT"
    assert SimulationExporter.map_request_stage("VERIFIED") == "STAGE_4_VERIFICATION"
    assert SimulationExporter.map_request_stage("IN_SERVICE") == "STAGE_5_SERVICE"
    assert SimulationExporter.map_request_stage("NEEDS_CORRECTION") == "STAGE_6_CORRECTION"
    assert SimulationExporter.map_request_stage("HUMAN_REVIEW") == "STAGE_7_HUMAN_REVIEW"
    assert SimulationExporter.map_request_stage("COMPLETED") == "STAGE_8_FINISHED"
    assert SimulationExporter.map_request_stage("REJECTED_INPUT") == "STAGE_8_FINISHED"
    assert SimulationExporter.map_request_stage("FAILED") == "STAGE_8_FINISHED"


# ============================================================================
# 2. Exporter & Atomic File Generation Tests
# ============================================================================

def test_generate_benchmark_replay_data():
    """Verify generated benchmark replay contains realistic multi-tick sequence with failure recovery."""
    manifest = SimulationExporter.generate_benchmark_replay_data(
        scenario_name="Automated Unit Test Benchmark",
        num_requests=12,
        num_request_agents=3,
    )

    assert manifest.schema_version == "1.0.0"
    assert manifest.total_ticks == 15
    assert len(manifest.snapshots) == 15
    assert len(manifest.events) > 0

    # Verify presence of supervisor timeout and reassignment events
    timeout_ev = next((e for e in manifest.events if "TIMEOUT" in e.event_type), None)
    assert timeout_ev is not None, "Expected an AGENT_TIMEOUT_DETECTED event in benchmark"
    assert timeout_ev.sender_agent == "AGT-SUPERVISOR-01"

    reassign_ev = next((e for e in manifest.events if "REASSIGN" in e.event_type), None)
    assert reassign_ev is not None, "Expected a TASK_REASSIGNED event in benchmark"
    assert reassign_ev.assignment_version == 2

    # Verify authoritative metrics
    assert manifest.metrics.total_requests == 12
    assert manifest.metrics.recovered_requests == 1
    assert manifest.metrics.message_integrity_rate == 100.0


def test_atomic_file_write(tmp_path):
    """Verify atomic write guarantees data persistence and removes temporary files."""
    test_file = str(tmp_path / "test_export.json")
    manifest = SimulationExporter.generate_benchmark_replay_data(
        output_path=test_file,
        num_requests=6,
    )

    assert os.path.exists(test_file)
    assert not os.path.exists(test_file + ".tmp"), "Temporary file should have been replaced"

    with open(test_file, "r", encoding="utf-8") as f:
        loaded = json.load(f)

    assert loaded["schema_version"] == "1.0.0"
    assert loaded["total_ticks"] == 15
    assert len(loaded["snapshots"]) == 15


def test_export_from_db(db_session: Session):
    """Verify export_from_db extracts live database records and maps them correctly."""
    # Seed a test request and agent in DB
    user = User(
        username="db_export_test_user",
        email="export_u@bankflow.test",
        password_hash=hash_password("Pass123!"),
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    cust = Customer(
        user_id=user.id,
        customer_code="CUST-EXP-01",
        full_name="Export Customer",
        email=user.email,
        phone="+1-555-0777",
        branch_id="BR-MAIN-001",
    )
    db_session.add(cust)
    db_session.flush()

    acc = Account(
        customer_id=cust.id,
        synthetic_account_number="ACC-EXP-01",
        account_type="SAVINGS",
        account_status="ACTIVE",
        branch_id="BR-MAIN-001",
    )
    db_session.add(acc)
    db_session.flush()

    req = Request(
        request_id="REQ-TEST-EXP-001",
        customer_id=cust.id,
        account_id=acc.id,
        service_type=ServiceType.CHEQUE_BOOK,
        request_status=RequestStatus.QUEUED,
        assignment_version=1,
        retry_count=0,
    )
    db_session.add(req)
    db_session.flush()

    agent = DBAgent(
        agent_code="RequestAgent_1",
        agent_type=AgentType.REQUEST,
        health_status=AgentHealthStatus.HEALTHY,
        availability_status="BUSY",
        processing_status="BUSY",
        current_request_id=req.id,
        completed_work_count=5,
        failed_work_count=0,
    )
    db_session.add(agent)
    db_session.flush()

    req.assigned_agent_id = agent.id
    db_session.commit()

    manifest = SimulationExporter.export_from_db(db_session, scenario_name="Test DB Export")

    assert manifest.schema_version == "1.0.0"
    assert manifest.scenario_name == "Test DB Export"
    assert manifest.metrics.total_requests >= 1

    # Check request token export
    found_req = next((r for r in manifest.snapshots[0].active_requests if r.request_id == "REQ-TEST-EXP-001"), None)
    assert found_req is not None
    assert found_req.stage == "STAGE_3_ASSIGNMENT"
    assert found_req.assigned_agent == "RequestAgent_1"

    # Check agent export
    found_agent = next((a for a in manifest.snapshots[0].agents if a.agent_code == "RequestAgent_1"), None)
    assert found_agent is not None
    assert found_agent.health_status == "HEALTHY"
    assert found_agent.processing_status == "BUSY"


# ============================================================================
# 3. FastAPI Simulation Visualization Endpoints Tests
# ============================================================================

def test_get_manifest_benchmark_endpoint(client: TestClient, bank_employee_auth):
    """Verify GET /api/bank/simulation/manifest?benchmark=true returns full manifest."""
    _, _, token = bank_employee_auth
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/bank/simulation/manifest?benchmark=true", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["schema_version"] == "1.0.0"
    assert data["total_ticks"] == 15
    assert len(data["snapshots"]) == 15
    assert "metrics" in data
    assert data["metrics"]["message_integrity_rate"] == 100.0


def test_get_snapshot_endpoint(client: TestClient, bank_employee_auth):
    """Verify GET /api/bank/simulation/snapshot returns latest tick snapshot."""
    _, _, token = bank_employee_auth
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/bank/simulation/snapshot", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert "tick" in data
    assert "active_requests" in data
    assert "agents" in data
    assert "queue_counts" in data


def test_post_export_endpoint(client: TestClient, bank_employee_auth):
    """Verify POST /api/bank/simulation/export triggers atomic export."""
    _, _, token = bank_employee_auth
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/api/bank/simulation/export?benchmark=true&output_filename=pytest_export.json",
        headers=headers,
    )
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "success"
    assert data["schema_version"] == "1.0.0"
    assert "pytest_export.json" in data["file_path"]
    assert os.path.exists(data["file_path"])


def test_simulation_endpoints_rbac(client: TestClient, customer_auth):
    """Verify customer role is strictly forbidden from bank simulation export endpoints."""
    _, _, token = customer_auth
    headers = {"Authorization": f"Bearer {token}"}

    # Customers must be rejected with 403 Forbidden
    resp1 = client.get("/api/bank/simulation/manifest", headers=headers)
    assert resp1.status_code == 403

    resp2 = client.get("/api/bank/simulation/snapshot", headers=headers)
    assert resp2.status_code == 403

    resp3 = client.post("/api/bank/simulation/export", headers=headers)
    assert resp3.status_code == 403
