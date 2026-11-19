"""
BankFlow AI - Agent Recovery and Fault Tolerance Router (Phase 8)
Exposes endpoints for supervisor health monitoring, failure telemetry,
automated/manual request reassignment, and chaos failure simulation.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.user import User
from app.models.failure_record import AgentFailure
from app.auth.dependencies import require_bank_employee, require_supervisor
from app.schemas.recovery import (
    RecoveryDashboardResponse,
    FailureRecordItem,
    ManualReassignPayload,
    CircuitBreakerStatusResponse,
    SimulateCrashPayload,
    SimulateHeartbeatPayload,
)
from app.services.recovery_service import AgentRecoveryService
from app.services.failure_simulation_service import FailureSimulationService
from app.messaging.circuit_breaker import rabbitmq_circuit_breaker

recovery_router = APIRouter(
    prefix="/api/bank/recovery",
    tags=["Agent Failure Recovery & Fault Tolerance"],
)


@recovery_router.get(
    "/dashboard",
    response_model=RecoveryDashboardResponse,
    summary="Agent Recovery & Reliability Dashboard Metrics",
)
def get_recovery_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_bank_employee),
):
    """
    Returns aggregated agent health, recovery statistics, circuit breaker status,
    and recent failure records for employee and supervisor dashboards.
    """
    return AgentRecoveryService.get_recovery_dashboard_metrics(db)


@recovery_router.get(
    "/failures",
    response_model=List[FailureRecordItem],
    summary="List Agent Failure Records",
)
def list_failures(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_bank_employee),
):
    """Lists recorded failure events with pagination."""
    offset = (page - 1) * page_size
    failures = (
        db.query(AgentFailure)
        .order_by(desc(AgentFailure.created_at))
        .offset(offset)
        .limit(page_size)
        .all()
    )
    return [
        FailureRecordItem(
            failure_id=f.failure_id,
            agent_code=f.agent_code,
            request_code=f.request_code,
            failure_type=f.failure_type,
            error_details=f.error_details,
            recovery_status=f.recovery_status,
            retry_count=f.retry_count,
            created_at=f.created_at.isoformat() if f.created_at else None,
            recovered_at=f.recovered_at.isoformat() if f.recovered_at else None,
        )
        for f in failures
    ]


@recovery_router.post(
    "/inspect",
    summary="Trigger On-Demand Agent Health Inspection",
)
def trigger_health_inspection(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_bank_employee),
):
    """Inspects agent heartbeat freshness and triggers automatic recovery of abandoned tasks."""
    return AgentRecoveryService.inspect_agents_health(db)


@recovery_router.post(
    "/tasks/{request_id}/retry",
    summary="Manually Retry Failed or Recovering Task",
)
def manual_retry_task(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_bank_employee),
):
    """Manually re-triggers automatic recovery and reassignment on an eligible failed task."""
    result = AgentRecoveryService.manual_retry_task(
        db=db,
        request_id=request_id,
        user_id=current_user.id,
    )
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Manual retry failed"),
        )
    return result


@recovery_router.post(
    "/tasks/{request_id}/reassign",
    summary="Manually Reassign Task to Target Agent",
)
def manual_reassign_task(
    request_id: str,
    payload: ManualReassignPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_bank_employee),
):
    """Manually reassigns a service request to a specified healthy agent."""
    result = AgentRecoveryService.manual_reassign_task(
        db=db,
        request_id=request_id,
        target_agent_code=payload.target_agent_code,
        user_id=current_user.id,
    )
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Manual reassignment failed"),
        )
    return result


@recovery_router.post(
    "/agents/{agent_code}/reset",
    summary="Reset Agent Health to HEALTHY",
)
def reset_agent_health(
    agent_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_bank_employee),
):
    """Marks an agent as healthy and available after resolving operational issues."""
    result = AgentRecoveryService.reset_agent_health(
        db=db,
        agent_code=agent_code,
        user_id=current_user.id,
    )
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("message", "Agent not found"),
        )
    return result


@recovery_router.post(
    "/agents/{agent_code}/pause",
    summary="Pause Agent Worker",
)
def pause_agent(
    agent_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_bank_employee),
):
    """Pauses an agent from accepting new service tasks."""
    return AgentRecoveryService.set_agent_pause_state(
        db=db,
        agent_code=agent_code,
        is_paused=True,
        user_id=current_user.id,
    )


@recovery_router.post(
    "/agents/{agent_code}/resume",
    summary="Resume Agent Worker",
)
def resume_agent(
    agent_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_bank_employee),
):
    """Resumes a paused agent back to active duty."""
    return AgentRecoveryService.set_agent_pause_state(
        db=db,
        agent_code=agent_code,
        is_paused=False,
        user_id=current_user.id,
    )


@recovery_router.get(
    "/circuit-breaker",
    response_model=CircuitBreakerStatusResponse,
    summary="Get RabbitMQ Circuit Breaker Status",
)
def get_circuit_breaker_status(
    current_user: User = Depends(require_bank_employee),
):
    """Returns real-time status of the dependency circuit breaker."""
    return rabbitmq_circuit_breaker.get_status()


@recovery_router.post(
    "/circuit-breaker/reset",
    summary="Reset RabbitMQ Circuit Breaker",
)
def reset_circuit_breaker(
    current_user: User = Depends(require_bank_employee),
):
    """Manually resets the dependency circuit breaker back to CLOSED."""
    rabbitmq_circuit_breaker.reset(reason=f"Manual reset by user '{current_user.username}'")
    return rabbitmq_circuit_breaker.get_status()


# ==============================================================================
# Failure Simulation Endpoints (Development & Chaos Testing)
# ==============================================================================

@recovery_router.post(
    "/simulation/crash",
    summary="Simulate Agent Crash",
)
def simulate_agent_crash(
    payload: SimulateCrashPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_bank_employee),
):
    """Forces an agent into FAILED status to test automatic recovery."""
    return FailureSimulationService.simulate_agent_crash(
        db=db,
        agent_code=payload.agent_code,
        reason=payload.reason or "Simulated crash event",
    )


@recovery_router.post(
    "/simulation/missed-heartbeat",
    summary="Simulate Missed Heartbeat",
)
def simulate_missed_heartbeat(
    payload: SimulateHeartbeatPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_bank_employee),
):
    """Sets an agent's heartbeat timestamp in the past to trigger timeout detection."""
    return FailureSimulationService.simulate_missed_heartbeat(
        db=db,
        agent_code=payload.agent_code,
        seconds_ago=payload.seconds_ago,
    )


@recovery_router.post(
    "/simulation/rabbitmq-outage",
    summary="Simulate RabbitMQ Outage (Trip Circuit Breaker)",
)
def simulate_rabbitmq_outage(
    current_user: User = Depends(require_bank_employee),
):
    """Trips the circuit breaker into OPEN state to simulate broker unavailability."""
    return FailureSimulationService.simulate_rabbitmq_outage()


@recovery_router.post(
    "/simulation/rabbitmq-restore",
    summary="Simulate RabbitMQ Restore (Reset Circuit Breaker)",
)
def simulate_rabbitmq_restore(
    current_user: User = Depends(require_bank_employee),
):
    """Resets the circuit breaker into CLOSED state to simulate broker restoration."""
    return FailureSimulationService.simulate_rabbitmq_restore()


@recovery_router.post(
    "/simulation/exhaust-retries/{request_id}",
    summary="Simulate Retry Exhaustion",
)
def simulate_retry_exhaustion(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_bank_employee),
):
    """Rapidly exhausts retry quota for a request to test escalation to HUMAN_REVIEW."""
    return FailureSimulationService.simulate_retry_exhaustion(
        db=db,
        request_id=request_id,
    )
