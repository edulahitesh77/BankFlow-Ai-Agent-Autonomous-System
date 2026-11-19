"""
BankFlow AI - Phase 8 Agent Failure Recovery & Fault Tolerance Test Suite
Tests heartbeat monitoring, failure detection, automatic reassignment,
exponential backoff, retry exhaustion, circuit breakers, idempotency, and audit trails.
"""

import sys
import os
import uuid
import time
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

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
from app.models.agent import Agent, AgentType, AgentHealthStatus
from app.models.failure_record import AgentFailure, FailureType, RecoveryStatus
from app.models.audit_log import AuditLog
from app.auth.security import hash_password
from app.auth.jwt_handler import create_access_token
from app.simulation.model import BankingSimulationModel
from app.simulation.agent_registry import AgentRegistry
from app.services.recovery_service import AgentRecoveryService
from app.services.retry_service import RecoveryRetryService
from app.services.failure_simulation_service import FailureSimulationService
from app.messaging.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerState,
    CircuitBreakerOpenException,
    rabbitmq_circuit_breaker,
)
from app.messaging.duplicate_protection import DuplicateProtectionService
from app.messaging.message_schema import StandardBankingMessage, BankingEventType


@pytest.fixture(scope="function")
def client(db_session: Session) -> TestClient:
    """Configures TestClient wired to the isolated transactional database session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def recovery_setup(db_session: Session):
    """Provisions test users, customer, accounts, agents, and auth headers."""
    # Ensure Mesa agents are synced into database
    sim = BankingSimulationModel()
    AgentRegistry.sync_agents_to_database(db_session, list(sim.agents))

    # 1. Customer User
    cust_user = User(
        username="rec_cust_01",
        email="rec_cust@bankflow.synthetic",
        password_hash=hash_password("Customer@2026!"),
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db_session.add(cust_user)
    db_session.flush()

    customer = Customer(
        user_id=cust_user.id,
        customer_code="CUST-REC-001",
        full_name="Recovery Test Customer",
        email=cust_user.email,
        phone="+1-555-8888",
        branch_id="BR-MAIN-001",
    )
    db_session.add(customer)
    db_session.flush()

    account = Account(
        customer_id=customer.id,
        synthetic_account_number="ACC-REC-0001",
        account_type="SAVINGS",
        account_status="ACTIVE",
        branch_id="BR-MAIN-001",
    )
    db_session.add(account)
    db_session.flush()

    # 2. Bank Staff User (Supervisor)
    staff_user = User(
        username="rec_supervisor_01",
        email="rec_supervisor@bankflow.synthetic",
        password_hash=hash_password("Staff@2026!"),
        role=UserRole.SUPERVISOR,
        is_active=True,
    )
    db_session.add(staff_user)
    db_session.flush()

    employee = Employee(
        user_id=staff_user.id,
        employee_code="EMP-REC-001",
        full_name="Operations Supervisor",
        department="Central Operations",
        designation="Lead Supervisor",
        branch_id="BR-MAIN-001",
    )
    db_session.add(employee)
    db_session.flush()

    # 3. Tokens & Headers
    cust_token = create_access_token(
        user_id=cust_user.id,
        role=cust_user.role.value,
        username=cust_user.username,
    )
    staff_token = create_access_token(
        user_id=staff_user.id,
        role=staff_user.role.value,
        username=staff_user.username,
    )

    cust_headers = {"Authorization": f"Bearer {cust_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    return {
        "customer_user": cust_user,
        "customer": customer,
        "account": account,
        "staff_user": staff_user,
        "employee": employee,
        "cust_headers": cust_headers,
        "staff_headers": staff_headers,
        "sim_model": sim,
    }


# ==============================================================================
# 1. HEARTBEAT & HEALTH MONITORING TESTS
# ==============================================================================

def test_heartbeat_monitoring_and_freshness_tracking(db_session: Session, recovery_setup):
    """Verify healthy agents periodically report heartbeats and persist timestamps."""
    agent = db_session.query(Agent).filter(Agent.agent_code == "RequestAgent_1").first()
    assert agent is not None

    initial_time = datetime.now(timezone.utc) - timedelta(seconds=10)
    agent.last_heartbeat_at = initial_time
    agent.health_status = AgentHealthStatus.HEALTHY.value
    db_session.commit()

    # Simulate agent sending heartbeat
    new_hb = datetime.now(timezone.utc)
    agent.last_heartbeat_at = new_hb
    agent.health_status = AgentHealthStatus.HEALTHY.value
    db_session.commit()
    db_session.refresh(agent)

    assert agent.last_heartbeat_at >= new_hb
    assert agent.health_status == "HEALTHY"


def test_unresponsive_agent_detection_on_missed_heartbeat(db_session: Session, recovery_setup):
    """Verify that an agent with stale heartbeats is detected as UNRESPONSIVE and logged."""
    agent = db_session.query(Agent).filter(Agent.agent_code == "RequestAgent_2").first()
    assert agent is not None

    # Simulate missed heartbeats exceeding timeout threshold
    stale_time = datetime.now(timezone.utc) - timedelta(seconds=60)
    agent.last_heartbeat_at = stale_time
    agent.last_active_at = stale_time
    agent.health_status = AgentHealthStatus.HEALTHY.value
    db_session.commit()

    # Trigger health inspection
    inspection = AgentRecoveryService.inspect_agents_health(db_session)

    db_session.refresh(agent)
    assert agent.health_status == AgentHealthStatus.UNRESPONSIVE.value
    assert inspection["unresponsive_detected"] >= 1

    # Verify FailureRecord was created
    failure = (
        db_session.query(AgentFailure)
        .filter(AgentFailure.agent_code == "RequestAgent_2")
        .order_by(AgentFailure.created_at.desc())
        .first()
    )
    assert failure is not None
    assert failure.failure_type == FailureType.UNRESPONSIVE_HEARTBEAT.value


# ==============================================================================
# 2. AUTOMATIC TASK RECOVERY & REASSIGNMENT TESTS
# ==============================================================================

def test_automatic_request_reassignment_from_failed_agent(db_session: Session, recovery_setup):
    """Verify that an abandoned request is atomically unassigned, incremented, and reallocated."""
    customer = recovery_setup["customer"]
    account = recovery_setup["account"]

    # 1. Create a service request assigned to RequestAgent_1
    agent_1 = db_session.query(Agent).filter(Agent.agent_code == "RequestAgent_1").first()
    agent_2 = db_session.query(Agent).filter(Agent.agent_code == "RequestAgent_2").first()
    assert agent_1 and agent_2

    # Ensure agent_2 is available to receive reassignment
    agent_2.availability_status = "AVAILABLE"
    agent_2.processing_status = "IDLE"
    agent_2.health_status = AgentHealthStatus.HEALTHY.value
    agent_2.current_request_id = None
    agent_2.is_paused = False

    req = Request(
        request_id=f"BFA-REQ-REC-{uuid.uuid4().hex[:6].upper()}",
        customer_id=customer.id,
        account_id=account.id,
        service_type=ServiceType.CHEQUE_BOOK,
        request_status=RequestStatus.QUEUED,
        priority="MEDIUM",
        assigned_agent_id=agent_1.id,
        assignment_version=0,
        retry_count=0,
        payload={"leaves": 25},
    )
    db_session.add(req)
    db_session.flush()

    agent_1.current_request_id = req.id
    agent_1.availability_status = "BUSY"
    agent_1.processing_status = "BUSY"
    db_session.commit()

    # 2. Simulate agent crash
    crash_res = FailureSimulationService.simulate_agent_crash(
        db=db_session,
        agent_code="RequestAgent_1",
        reason="Process terminated by OOM killer",
    )
    assert crash_res["success"] is True

    # 3. Trigger automatic recovery
    recovery_res = AgentRecoveryService.recover_abandoned_task(
        db=db_session,
        request_id_or_code=req.request_id,
        failed_agent_code="RequestAgent_1",
        failure_type=FailureType.CRASH_DURING_EXECUTION,
        error_details="Process terminated by OOM killer",
    )

    db_session.refresh(req)
    db_session.refresh(agent_1)

    assert recovery_res["status"] in ("REASSIGNED", "QUEUED_FOR_RECOVERY")
    assert req.assignment_version == 1
    assert req.retry_count == 1
    assert agent_1.current_request_id is None

    # If reassigned to agent_2
    if recovery_res["status"] == "REASSIGNED":
        db_session.refresh(agent_2)
        assert req.assigned_agent_id == agent_2.id
        assert agent_2.current_request_id == req.id


def test_stale_agent_cannot_complete_reassigned_task(db_session: Session, recovery_setup):
    """Verify that a stale agent holding an older assignment version cannot complete the request."""
    customer = recovery_setup["customer"]
    account = recovery_setup["account"]

    req = Request(
        request_id=f"BFA-REQ-STALE-{uuid.uuid4().hex[:6].upper()}",
        customer_id=customer.id,
        account_id=account.id,
        service_type=ServiceType.DEBIT_CARD_REPLACEMENT,
        request_status=RequestStatus.QUEUED,
        priority="MEDIUM",
        assignment_version=2,  # Current DB version is 2
        retry_count=1,
        payload={"reason": "DAMAGED"},
    )
    db_session.add(req)
    db_session.commit()

    # Create Mesa agent with stale version 1
    sim = recovery_setup["sim_model"]
    stale_agent = sim.get_request_agents()[0]
    stale_agent.assigned_version = 1  # Older than DB version 2
    stale_agent.current_request_id = req.request_id
    initial_completed_count = stale_agent.completed_work_count

    # Stale agent tries to complete the request
    stale_agent.complete_and_release(db_session, req, final_status=RequestStatus.COMPLETED)

    # Verifies completion was rejected due to version mismatch
    assert stale_agent.completed_work_count == initial_completed_count
    db_session.refresh(req)
    assert req.request_status != RequestStatus.COMPLETED


# ==============================================================================
# 3. RETRY POLICY & EXPONENTIAL BACKOFF TESTS
# ==============================================================================

def test_retry_exponential_backoff_calculation():
    """Verify mathematical accuracy of exponential backoff delay calculation."""
    # Attempt 1: 2.0s
    d1 = RecoveryRetryService.calculate_backoff_delay(1)
    assert d1 == 2.0

    # Attempt 2: 4.0s
    d2 = RecoveryRetryService.calculate_backoff_delay(2)
    assert d2 == 4.0

    # Attempt 3: 8.0s
    d3 = RecoveryRetryService.calculate_backoff_delay(3)
    assert d3 == 8.0

    # High attempt: bounded by max delay
    d10 = RecoveryRetryService.calculate_backoff_delay(10)
    assert d10 <= settings.RECOVERY_MAX_RETRY_DELAY_SECONDS


def test_retry_limit_enforcement_escalates_to_human_review(db_session: Session, recovery_setup):
    """Verify that exhausting max retries escalates task to HUMAN_REVIEW rather than discarding."""
    customer = recovery_setup["customer"]
    account = recovery_setup["account"]

    req = Request(
        request_id=f"BFA-REQ-MAXRETRY-{uuid.uuid4().hex[:6].upper()}",
        customer_id=customer.id,
        account_id=account.id,
        service_type=ServiceType.ADDRESS_UPDATE,
        request_status=RequestStatus.QUEUED,
        priority="HIGH",
        assignment_version=3,
        retry_count=settings.RECOVERY_MAX_RETRIES,  # Already at max retries (3)
        payload={"new_synthetic_address": "456 Recovery Lane"},
    )
    db_session.add(req)
    db_session.commit()

    # Trigger recovery when retries are already exhausted
    result = AgentRecoveryService.recover_abandoned_task(
        db=db_session,
        request_id_or_code=req.request_id,
        failure_type=FailureType.REPEATED_PROCESSING_FAILURE,
        error_details="Persistent agent connection crash",
    )

    db_session.refresh(req)
    assert result["status"] == "ESCALATED"
    assert req.request_status == RequestStatus.HUMAN_REVIEW
    assert req.review_required is True
    assert req.reason_code == "RECOVERY_RETRIES_EXHAUSTED"


def test_non_retryable_error_immediately_escalates():
    """Verify deterministic errors are classified as non-retryable and not retried endlessly."""
    assert RecoveryRetryService.is_retryable_error("Agent socket timeout") is True
    assert RecoveryRetryService.is_retryable_error("Unexpected server crash") is True

    # Deterministic failures
    assert RecoveryRetryService.is_retryable_error("Invalid leaf count: 75") is False
    assert RecoveryRetryService.is_retryable_error("Prerequisite account closed") is False
    assert RecoveryRetryService.is_retryable_error("Schema violation: missing fields") is False


# ==============================================================================
# 4. CIRCUIT BREAKER & EXTERNAL DEPENDENCY TESTS
# ==============================================================================

def test_circuit_breaker_state_transitions():
    """Verify CLOSED -> OPEN -> HALF_OPEN -> CLOSED state lifecycle."""
    cb = CircuitBreaker(
        name="TestCircuit",
        failure_threshold=2,
        recovery_timeout_seconds=0.2,  # 200ms
        half_open_max_requests=1,
    )

    assert cb.state == CircuitBreakerState.CLOSED
    assert cb.can_execute() is True

    # 1st failure: remains CLOSED
    cb.record_failure(ValueError("Blip 1"))
    assert cb.state == CircuitBreakerState.CLOSED

    # 2nd failure: trips to OPEN
    cb.record_failure(ValueError("Blip 2"))
    assert cb.state == CircuitBreakerState.OPEN
    assert cb.can_execute() is False

    # Wait for recovery timeout
    time.sleep(0.25)

    # Next check auto-transitions to HALF_OPEN
    assert cb.state == CircuitBreakerState.HALF_OPEN
    assert cb.can_execute() is True

    # Successful canary test resets back to CLOSED
    cb.record_success()
    assert cb.state == CircuitBreakerState.CLOSED
    assert cb.can_execute() is True


def test_circuit_breaker_rejects_calls_when_open():
    """Verify that calling an operation while circuit breaker is OPEN raises CircuitBreakerOpenException."""
    cb = CircuitBreaker(
        name="MockBroker",
        failure_threshold=1,
        recovery_timeout_seconds=10.0,
    )
    cb.trip("Simulated network isolation")

    def target_call():
        return "success"

    with pytest.raises(CircuitBreakerOpenException):
        cb.call(target_call)


# ==============================================================================
# 5. IDEMPOTENCY & CONCURRENCY TESTS
# ==============================================================================

def test_concurrency_and_single_ownership_protection(db_session: Session, recovery_setup):
    """Verify that multiple agents competing for the same request atomically results in exactly one owner."""
    customer = recovery_setup["customer"]
    account = recovery_setup["account"]

    req = Request(
        request_id=f"BFA-REQ-COMPETE-{uuid.uuid4().hex[:6].upper()}",
        customer_id=customer.id,
        account_id=account.id,
        service_type=ServiceType.CHEQUE_BOOK,
        request_status=RequestStatus.CLASSIFIED,
        priority="MEDIUM",
        assignment_version=0,
        payload={"leaves": 25},
    )
    db_session.add(req)
    db_session.commit()

    res = FailureSimulationService.simulate_competing_agents(
        db=db_session,
        request_id=req.request_id,
        agent_codes=["RequestAgent_1", "RequestAgent_2", "RequestAgent_3"],
    )

    assert res["success"] is True
    assert res["claimed_by"] == "RequestAgent_1"
    assert "RequestAgent_2" in res["rejected_agents"]
    assert "RequestAgent_3" in res["rejected_agents"]


def test_duplicate_message_idempotency_does_not_duplicate_recovery(db_session: Session):
    """Verify that consuming duplicate messages avoids executing tasks twice."""
    msg = StandardBankingMessage(
        request_id="REQ-DUP-TEST-001",
        request_version=0,
        sender_agent_id="AGT-CUST-SIM-01",
        receiver_agent_id="AGT-INTAKE-01",
        event_type=BankingEventType.REQUEST_CREATED,
        payload={"service": "CHEQUE_BOOK"},
    )

    is_dup1, _ = DuplicateProtectionService.record_received_message(
        db=db_session,
        message=msg,
        consumer_name="TestConsumer",
    )
    assert is_dup1 is False

    is_dup2, _ = DuplicateProtectionService.record_received_message(
        db=db_session,
        message=msg,
        consumer_name="TestConsumer",
    )
    assert is_dup2 is True


# ==============================================================================
# 6. REST API & RBAC AUTHORIZATION TESTS
# ==============================================================================

def test_supervisor_access_recovery_dashboard_and_failures(client: TestClient, recovery_setup):
    """Verify supervisor can access recovery dashboard metrics and failure history."""
    headers = recovery_setup["staff_headers"]

    resp = client.get("/api/bank/recovery/dashboard", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "agents_summary" in data
    assert "requests_summary" in data
    assert "circuit_breaker" in data
    assert "recent_failures" in data


def test_manual_recovery_retry_and_reassign_by_staff(client: TestClient, db_session: Session, recovery_setup):
    """Verify staff can manually retry and reassign requests via REST endpoints."""
    headers = recovery_setup["staff_headers"]
    customer = recovery_setup["customer"]
    account = recovery_setup["account"]

    req = Request(
        request_id=f"BFA-REQ-MANUAL-{uuid.uuid4().hex[:6].upper()}",
        customer_id=customer.id,
        account_id=account.id,
        service_type=ServiceType.CHEQUE_BOOK,
        request_status=RequestStatus.QUEUED,
        priority="MEDIUM",
        assignment_version=1,
        retry_count=1,
        payload={"leaves": 50},
    )
    db_session.add(req)
    db_session.commit()

    # Manual retry endpoint
    retry_resp = client.post(f"/api/bank/recovery/tasks/{req.request_id}/retry", headers=headers)
    assert retry_resp.status_code == 200
    assert retry_resp.json()["success"] is True

    # Manual reassign endpoint
    reassign_resp = client.post(
        f"/api/bank/recovery/tasks/{req.request_id}/reassign",
        headers=headers,
        json={"target_agent_code": "RequestAgent_1"},
    )
    assert reassign_resp.status_code == 200
    assert reassign_resp.json()["success"] is True
    assert reassign_resp.json()["assigned_to"] == "RequestAgent_1"


def test_customer_forbidden_from_recovery_endpoints(client: TestClient, recovery_setup):
    """Verify that customer tokens are forbidden from accessing recovery and chaos endpoints."""
    headers = recovery_setup["cust_headers"]

    # 1. Recovery dashboard
    r1 = client.get("/api/bank/recovery/dashboard", headers=headers)
    assert r1.status_code == 403

    # 2. Failure list
    r2 = client.get("/api/bank/recovery/failures", headers=headers)
    assert r2.status_code == 403

    # 3. Health inspection
    r3 = client.post("/api/bank/recovery/inspect", headers=headers)
    assert r3.status_code == 403

    # 4. Chaos simulation
    r4 = client.post(
        "/api/bank/recovery/simulation/crash",
        headers=headers,
        json={"agent_code": "RequestAgent_1"},
    )
    assert r4.status_code == 403


# ==============================================================================
# 7. CUSTOMER NOTIFICATION & AUDIT LOGGING TESTS
# ==============================================================================

def test_customer_status_message_on_delayed_requests(client: TestClient, db_session: Session, recovery_setup):
    """Verify that delayed requests show reassuring messages without leaking technical error details."""
    customer = recovery_setup["customer"]
    account = recovery_setup["account"]
    headers = recovery_setup["cust_headers"]

    req = Request(
        request_id=f"BFA-REQ-NOTIF-{uuid.uuid4().hex[:6].upper()}",
        customer_id=customer.id,
        account_id=account.id,
        service_type=ServiceType.CHEQUE_BOOK,
        request_status=RequestStatus.QUEUED,
        priority="MEDIUM",
        assignment_version=2,
        retry_count=1,  # Retried at least once -> delayed
        payload={"leaves": 25},
    )
    db_session.add(req)
    db_session.commit()

    resp = client.get(f"/api/customer/requests/{req.request_id}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["retry_count"] == 1
    assert data["customer_status_message"] == "Your request is taking longer than expected. Our team is monitoring it."
    # Ensure raw internal errors or stack traces are NOT in customer response
    assert "error_details" not in data
    assert "stack_trace" not in data


def test_audit_logging_created_for_all_recovery_actions(db_session: Session, recovery_setup):
    """Verify that automated recovery and manual actions generate structured audit trail records."""
    customer = recovery_setup["customer"]
    account = recovery_setup["account"]

    req = Request(
        request_id=f"BFA-REQ-AUDIT-{uuid.uuid4().hex[:6].upper()}",
        customer_id=customer.id,
        account_id=account.id,
        service_type=ServiceType.CHEQUE_BOOK,
        request_status=RequestStatus.QUEUED,
        priority="MEDIUM",
        assignment_version=0,
        retry_count=0,
        payload={"leaves": 25},
    )
    db_session.add(req)
    db_session.commit()

    # Trigger recovery
    AgentRecoveryService.recover_abandoned_task(
        db=db_session,
        request_id_or_code=req.request_id,
        failure_type=FailureType.CRASH_DURING_EXECUTION,
        error_details="Simulated failure for audit verification",
    )

    # Check AuditLog table
    audit_logs = (
        db_session.query(AuditLog)
        .filter(AuditLog.request_id == req.request_id)
        .all()
    )
    actions = [a.action for a in audit_logs]
    assert any("RECOVERED" in act or "QUEUED_FOR_RECOVERY" in act for act in actions)
