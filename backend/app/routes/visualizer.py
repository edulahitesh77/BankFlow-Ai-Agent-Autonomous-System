"""
BankFlow AI - Visualizer Routes
Provides endpoints for the AI Workflow Visualizer canvas, request journey inspector,
rule-based decision analysis, and real-time performance analytics.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query, Path, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.auth.dependencies import require_bank_employee
from app.services.visualizer_service import VisualizerService
from app.simulation.exporter import SimulationExporter


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
