"""
BankFlow AI - Visualizer Routes
Provides endpoints for the AI Workflow Visualizer canvas, request journey inspector,
rule-based decision analysis, and real-time performance analytics.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, Path, Body, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.user import User
from app.auth.dependencies import require_bank_employee
from app.services.visualizer_service import VisualizerService
from app.simulation.exporter import SimulationExporter


class FederationSimulatePayload(BaseModel):
    source_branch_id: str = Field("BLR001", description="Originating branch code")
    destination_branch_id: str = Field("CHE001", description="Target destination branch code")
    requested_scope: str = Field("ACCOUNT_STATUS_CONFIRMATION", description="Permitted or requested scope")
    auth_mode: str = Field("VALID", description="VALID | INVALID_KEY | UNREGISTERED_BRANCH | DUPLICATE_REPLAY | OUTSIDE_SCOPE")


class SecurityScenarioPayload(BaseModel):
    scenario_id: str = Field(..., description="Scenario ID to execute")


class RecoverySimulatePayload(BaseModel):
    failed_agent_code: str = Field("AGT-REQ-01", description="Agent code to fail and recover")


router = APIRouter(prefix="/api/bank/visualizer", tags=["AI Workflow Visualizer"])


@router.get(
    "/recent-requests",
    response_model=List[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Get recent requests for journey selector",
)
def get_recent_requests(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
):
    """Returns recent requests with status and customer names for the journey selector."""
    return VisualizerService.get_recent_requests(db, limit=limit)


@router.get(
    "/request-journey/{request_id}",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Inspect complete end-to-end journey of a request",
)
def get_request_journey(
    request_id: str = Path(..., description="Unique Request Identifier (e.g. REQ-...)"),
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
):
    """Reconstructs the full end-to-end journey of a request across all agents and states."""
    return VisualizerService.get_request_journey(db, request_id=request_id)


@router.get(
    "/decisions",
    response_model=List[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Get recorded rule-based agent decisions",
)
def get_decisions(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
):
    """Retrieves authentic rule-based decisions executed by Intake, Dispatcher, and Verification agents."""
    return VisualizerService.get_decision_records(db, limit=limit)


@router.get(
    "/analytics",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get live performance and agent utilization analytics",
)
def get_analytics(
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
):
    """Calculates agent utilization, request throughput, and recovery telemetry."""
    return VisualizerService.get_analytics_summary(db)


@router.get(
    "/replay-manifest",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get simulation manifest for visualizer replay mode",
)
def get_replay_manifest(
    scenario_name: str = Query("Default Production Scenario"),
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
):
    """Provides recorded simulation timeline frames for client-side visual replay."""
    manifest = SimulationExporter.export_from_db(db, scenario_name=scenario_name)
    return manifest.model_dump()


# =============================================================================
# FEDERATION NETWORK VISUALIZATION ENDPOINTS
# =============================================================================

@router.get(
    "/federation/topology",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get multi-branch federation topology and recent cross-branch events",
)
def get_federation_topology(
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
):
    """Returns branches BLR001, CHE001, HYD001, Central Gateway node, and real events."""
    return VisualizerService.get_federation_topology(db)


@router.post(
    "/federation/simulate-exchange",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Execute authentic cross-branch exchange and generate animated trajectory",
)
def simulate_federation_exchange(
    payload: FederationSimulatePayload,
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
):
    """Executes real inter-branch request through Federation Gateway and returns packet journey."""
    return VisualizerService.simulate_federation_exchange(
        db=db,
        source_branch_id=payload.source_branch_id,
        destination_branch_id=payload.destination_branch_id,
        requested_scope=payload.requested_scope,
        auth_mode=payload.auth_mode,
    )


# =============================================================================
# SECURITY OPERATIONS & ATTACK/DEFENSE SCENARIOS
# =============================================================================

@router.get(
    "/security/overview",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get backend security architecture parameters and audit trail",
)
def get_security_overview(
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
):
    """Retrieves verified configuration for Argon2id, JWT, AES-256-GCM, TLS, and RBAC."""
    return VisualizerService.get_security_overview(db)


@router.post(
    "/security/execute-scenario",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Run controlled security attack/defense scenario using backend security engines",
)
def execute_security_scenario(
    payload: SecurityScenarioPayload,
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
):
    """Executes one of the 7 authentic security verification scenarios and logs real audit trail."""
    return VisualizerService.execute_security_scenario(db, scenario_id=payload.scenario_id)


# =============================================================================
# RECOVERY SEQUENCE ENDPOINTS
# =============================================================================

@router.get(
    "/recovery/sequence",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get recent supervisor recovery sequence",
)
def get_recovery_sequence(
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
):
    """Retrieves real agent failure and recovery events from PostgreSQL."""
    return VisualizerService.get_recovery_sequence(db)


@router.post(
    "/recovery/simulate-recovery",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Trigger real controlled supervisor failure and reassignment sequence",
)
def simulate_recovery_sequence(
    payload: RecoverySimulatePayload,
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
):
    """Performs agent failure detection, task isolation, and atomic worker reassignment."""
    return VisualizerService.simulate_recovery_sequence(db, failed_agent_code=payload.failed_agent_code)

