"""
BankFlow AI - Simulation Management Routes
Protected endpoints accessible strictly by internal BANK_EMPLOYEE staff.
Controls Mesa simulation background execution and executes synthetic test benchmarks.
"""

import os
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.auth.dependencies import require_bank_employee
from app.schemas.agent_simulation import (
    SimulationStartRequest,
    SimulationStatusResponse,
    SimulationStatisticsResponse,
    RunTestScenarioRequest,
    RunTestScenarioResponse,
)
from app.schemas.unity_export import (
    SimulationManifestExport,
    SimulationSnapshotExport,
)
from app.simulation.exporter import SimulationExporter
from app.services.agent_service import AgentService

router = APIRouter(prefix="/api/bank/simulation", tags=["Simulation Engine"])


@router.post(
    "/start",
    status_code=status.HTTP_200_OK,
    summary="Start background multi-agent simulation",
    description="Initiates background Mesa simulation loop across Request and Service agent pools.",
)
def start_simulation(
    config: SimulationStartRequest = SimulationStartRequest(),
    current_user: User = Depends(require_bank_employee),
) -> Dict[str, Any]:
    """Start the multi-agent simulation."""
    return AgentService.start_simulation(config)


@router.post(
    "/stop",
    status_code=status.HTTP_200_OK,
    summary="Stop background multi-agent simulation",
    description="Safely terminates background simulation ticks.",
)
def stop_simulation(
    current_user: User = Depends(require_bank_employee),
) -> Dict[str, Any]:
    """Stop the multi-agent simulation."""
    return AgentService.stop_simulation()


@router.get(
    "/status",
    response_model=SimulationStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current simulation status",
    description="Returns live tick counter, active workers, scenario name, and recent logs.",
)
def get_simulation_status(
    current_user: User = Depends(require_bank_employee),
) -> SimulationStatusResponse:
    """Retrieve operational status of the simulation."""
    return AgentService.get_simulation_status()


@router.get(
    "/statistics",
    response_model=SimulationStatisticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get simulation throughput statistics",
    description="Returns aggregate counts of processed, completed, human review, and active requests.",
)
def get_simulation_statistics(
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
) -> SimulationStatisticsResponse:
    """Retrieve simulation throughput metrics."""
    return AgentService.get_simulation_statistics(db)


@router.post(
    "/run-test",
    response_model=RunTestScenarioResponse,
    status_code=status.HTTP_200_OK,
    summary="Run controlled synthetic benchmark scenario",
    description="Executes a deterministic multi-agent scenario (1: Normal, 2: High Load, 3: Incomplete, 4: Mixed, 5: Human Review).",
)
def run_test_scenario(
    req: RunTestScenarioRequest,
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
) -> RunTestScenarioResponse:
    """Execute a scenario benchmark."""
    return AgentService.run_test_scenario(req, db)


@router.get(
    "/manifest",
    response_model=SimulationManifestExport,
    status_code=status.HTTP_200_OK,
    summary="Get simulation manifest for Unity dashboard",
    description="Returns complete simulation manifest with snapshots, events, and metrics.",
)
def get_simulation_manifest(
    benchmark: bool = False,
    scenario_name: str = "Live Production State",
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
) -> SimulationManifestExport:
    """Retrieve simulation manifest for Unity visualization."""
    if benchmark:
        return SimulationExporter.generate_benchmark_replay_data(scenario_name=scenario_name)
    return SimulationExporter.export_from_db(db, scenario_name=scenario_name)


@router.get(
    "/snapshot",
    response_model=SimulationSnapshotExport,
    status_code=status.HTTP_200_OK,
    summary="Get current tick simulation snapshot",
    description="Returns live tick snapshot of active requests, agent statuses, and queue counts for Unity Live Monitoring.",
)
def get_simulation_snapshot(
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
) -> SimulationSnapshotExport:
    """Retrieve the latest simulation tick snapshot."""
    manifest = SimulationExporter.export_from_db(db)
    if manifest.snapshots:
        return manifest.snapshots[-1]
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No simulation snapshot available.")


@router.post(
    "/export",
    status_code=status.HTTP_200_OK,
    summary="Export simulation data to JSON file",
    description="Atomically exports simulation manifest to disk for Unity 2D Replay mode.",
)
def export_simulation(
    benchmark: bool = False,
    output_filename: str = "exported_simulation.json",
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Export simulation data to disk atomically."""
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    target_dir = os.path.join(backend_dir, "unity-dashboard", "Assets", "Data")
    os.makedirs(target_dir, exist_ok=True)

    safe_name = os.path.basename(output_filename)
    if not safe_name.endswith(".json"):
        safe_name += ".json"
    target_path = os.path.join(target_dir, safe_name)

    if benchmark:
        manifest = SimulationExporter.generate_benchmark_replay_data(output_path=target_path)
    else:
        manifest = SimulationExporter.export_from_db(db, output_path=target_path)

    return {
        "status": "success",
        "message": f"Successfully exported simulation manifest to {safe_name}",
        "file_path": target_path,
        "total_ticks": manifest.total_ticks,
        "total_events": manifest.total_events,
        "schema_version": manifest.schema_version,
    }

