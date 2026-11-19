"""
BankFlow AI - Agent Management Routes
Protected endpoints accessible strictly by internal BANK_EMPLOYEE staff.
Provides multi-agent swarm status, individual agent introspection, and workload telemetry.
"""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.auth.dependencies import require_bank_employee
from app.schemas.agent_simulation import (
    AgentListResponse,
    AgentDetailResponse,
    AgentStatisticsResponse,
)
from app.schemas.messaging import AgentCommunicationMetric
from app.services.agent_service import AgentService
from app.messaging.broker_service import BrokerService

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
