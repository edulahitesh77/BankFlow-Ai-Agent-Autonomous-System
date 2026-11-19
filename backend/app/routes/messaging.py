"""
BankFlow AI - Messaging and Communication Routes
Protected endpoints accessible strictly by internal BANK_EMPLOYEE staff.
Provides broker monitoring, queue statistics, event history, dead-letter inspection, and message replay.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.auth.dependencies import require_bank_employee
from app.messaging.broker_service import BrokerService
from app.messaging.dead_letter import DeadLetterService
from app.schemas.messaging import (
    BrokerStatusResponse,
    QueueStatusItem,
    EventHistoryResponse,
    AgentEventItem,
    DeadLetterListResponse,
    RetryMessageResponse,
    CommunicationStatisticsResponse,
)

router = APIRouter(prefix="/api/bank/messaging", tags=["Multi-Agent Messaging"])


@router.get(
    "/status",
    response_model=BrokerStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get RabbitMQ connection and topology status",
    description="Returns broker connection health, exchange names, and virtual host details without exposing credentials.",
)
def get_broker_status(
    current_user: User = Depends(require_bank_employee),
) -> BrokerStatusResponse:
    """Retrieve RabbitMQ broker connectivity and exchange topology."""
    return BrokerService.get_broker_status()


@router.get(
    "/queues",
    response_model=List[QueueStatusItem],
    status_code=status.HTTP_200_OK,
    summary="Get RabbitMQ queue depths and consumers",
    description="Returns message count and consumer count for all durable agent queues.",
)
def get_queues_status(
    current_user: User = Depends(require_bank_employee),
) -> List[QueueStatusItem]:
    """Inspect durable queue depths."""
    return BrokerService.get_queues_status()


@router.get(
    "/statistics",
    response_model=CommunicationStatisticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get communication throughput statistics",
    description="Returns total messages published, consumed, processed, duplicates caught, and retries.",
)
def get_communication_statistics(
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
) -> CommunicationStatisticsResponse:
    """Aggregate broker throughput telemetry."""
    return BrokerService.get_communication_statistics(db)


@router.get(
    "/events",
    response_model=EventHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get agent communication events history",
    description="Returns paginated, filterable event records stored in PostgreSQL.",
)
def get_events_history(
    request_id: Optional[str] = Query(None, description="Filter by request ID substring"),
    event_type: Optional[str] = Query(None, description="Filter by event type (e.g. REQUEST_CREATED)"),
    agent_id: Optional[str] = Query(None, description="Filter by publishing agent code"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
) -> EventHistoryResponse:
    """List agent communication events."""
    return BrokerService.get_events_history(
        db=db,
        request_id=request_id,
        event_type=event_type,
        agent_id=agent_id,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/events/{request_id}",
    response_model=List[AgentEventItem],
    status_code=status.HTTP_200_OK,
    summary="Get communication timeline for a specific request",
    description="Returns chronological exchange history showing all messages exchanged during request processing.",
)
def get_request_communication_timeline(
    request_id: str,
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
) -> List[AgentEventItem]:
    """Retrieve full chronological conversation timeline for a single request."""
    return BrokerService.get_request_communication_timeline(db, request_id)


@router.get(
    "/dead-letter",
    response_model=DeadLetterListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get dead letter messages",
    description="Lists failed messages that exceeded retry budgets or encountered fatal processing errors.",
)
def list_dead_letters(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
) -> DeadLetterListResponse:
    """List dead letter queue messages."""
    return DeadLetterService.list_dead_letters(db, page=page, page_size=page_size)


@router.post(
    "/retry/{message_id}",
    response_model=RetryMessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Retry a dead letter message",
    description="Safely re-queues a failed message with a fresh retry budget and staff audit trail.",
)
def retry_dead_letter_message(
    message_id: str,
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
) -> RetryMessageResponse:
    """Replay a dead-letter message."""
    officer_name = current_user.username
    return DeadLetterService.retry_dead_letter_message(db, message_id, officer_name)
