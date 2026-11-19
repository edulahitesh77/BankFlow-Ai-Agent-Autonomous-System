"""
BankFlow AI - Agent Management Routes
Protected endpoints accessible strictly by internal BANK_EMPLOYEE staff.
Provides multi-agent swarm status, individual agent introspection, and workload telemetry.
"""

import asyncio
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, status, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session
from app.database import get_db, SessionLocal
from app.models.user import User, UserRole
from app.auth.dependencies import require_bank_employee
from app.auth.jwt_handler import decode_access_token
from app.schemas.agent_simulation import (
    AgentListResponse,
    AgentDetailResponse,
    AgentStatisticsResponse,
    RealtimeMonitoringResponse,
)
from app.schemas.messaging import AgentCommunicationMetric
from app.services.agent_service import AgentService
from app.messaging.broker_service import BrokerService

logger = logging.getLogger("bankflow_ai.routes.agents")

router = APIRouter(prefix="/api/bank/agents", tags=["Multi-Agent System"])


@router.get(
    "/statistics",
    response_model=AgentStatisticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get multi-agent swarm statistics",
    description="Returns aggregate availability, busy count, and total work processed across all agents.",
)
def get_agent_statistics(
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
) -> AgentStatisticsResponse:
    """Retrieve swarm availability telemetry."""
    return AgentService.get_agent_statistics(db)


@router.get(
    "/communication",
    response_model=List[AgentCommunicationMetric],
    status_code=status.HTTP_200_OK,
    summary="Get communication statistics by agent",
    description="Returns message publication, task consumption, and heartbeat telemetry per agent.",
)
def get_agent_communication_metrics(
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
) -> List[AgentCommunicationMetric]:
    """Retrieve communication metrics per agent."""
    return BrokerService.get_agent_communication_metrics(db)


@router.get(
    "",
    response_model=AgentListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get all agents in the multi-agent system",
    description="Returns active agent instances, current assignments, and availability.",
)
def get_all_agents(
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
) -> AgentListResponse:
    """List all agent instances."""
    return AgentService.get_all_agents(db)


@router.get(
    "/realtime-monitoring",
    response_model=RealtimeMonitoringResponse,
    status_code=status.HTTP_200_OK,
    summary="Get complete real-time multi-agent monitoring snapshot",
    description="Returns live operational status of all agents (Customer, Intake, Verification, Request pool, Service pool, Supervisor), active assignments, pipeline stages, and event streams.",
)
def get_realtime_monitoring_snapshot(
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
) -> RealtimeMonitoringResponse:
    """Retrieve full real-time agent telemetry snapshot."""
    return AgentService.get_realtime_monitoring_data(db)


@router.websocket("/ws")
async def websocket_agent_monitoring(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
):
    """
    WebSocket endpoint streaming live multi-agent swarm updates every 1.5 seconds.
    Requires valid JWT token authentication belonging to BANK_EMPLOYEE, SUPERVISOR, or ADMINISTRATOR.
    """
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        payload = decode_access_token(token)
        if not payload or payload.get("role") not in [
            UserRole.BANK_EMPLOYEE.value,
            UserRole.SUPERVISOR.value,
            UserRole.ADMINISTRATOR.value,
        ]:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    except Exception as auth_err:
        logger.warning("WebSocket authentication failed: %s", auth_err)
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    logger.info("WebSocket agent monitoring client connected (User: %s)", payload.get("sub"))

    try:
        while True:
            db: Session = SessionLocal()
            try:
                data = AgentService.get_realtime_monitoring_data(db)
                await websocket.send_json(data)
            finally:
                db.close()
            await asyncio.sleep(1.5)
    except WebSocketDisconnect:
        logger.info("WebSocket agent monitoring client disconnected.")
    except Exception as e:
        logger.error("WebSocket agent monitoring error: %s", str(e))


@router.get(
    "/{agent_id}",
    response_model=AgentDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get individual agent details",
    description="Inspect single agent properties, current request, and completed work count.",
)
def get_agent_details(
    agent_id: str,
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
) -> AgentDetailResponse:
    """Retrieve individual agent telemetry."""
    return AgentService.get_agent_by_id(db, agent_id)
