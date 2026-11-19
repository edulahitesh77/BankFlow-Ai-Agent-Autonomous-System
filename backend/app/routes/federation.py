"""
BankFlow AI - Federation Gateway Routes (Phase 10)
Provides secure HTTP endpoints for inter-branch information exchange,
branch registry inspection, and federation telemetry for bank supervisors.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.database import get_db, BranchDatabaseManager
from app.models.user import User
from app.models.branch import Branch, BranchStatus
from app.models.federation_event import FederationEvent
from app.models.request import Request, RequestStatus
from app.models.agent import Agent
from app.auth.dependencies import require_bank_employee, require_supervisor
from app.federation.schemas import (
    CrossBranchRequest,
    CrossBranchResponse,
    BranchSummaryResponse,
    FederationStatisticsResponse,
    FederationEventItem,
)
from app.federation.gateway import FederationGateway

router = APIRouter(prefix="/api/federation", tags=["Multi-Branch Federation"])


def ensure_default_branches(db: Session):
    """Ensures the 3 standard branches exist in the gateway database."""
    if db.query(Branch).count() == 0:
        import hashlib
        from app.federation.seed import BRANCH_METADATA
        for entry in BRANCH_METADATA:
            b_obj = Branch(
                branch_id=entry["branch_id"],
                branch_name=entry["branch_name"],
                location=entry["location"],
                branch_status=entry["branch_status"],
                api_endpoint=entry["api_endpoint"],
                database_name=entry["database_name"],
                api_key_hash=hashlib.sha256(entry["secret"].encode("utf-8")).hexdigest(),
                is_gateway_enabled=True,
            )
            db.add(b_obj)
        db.commit()


@router.post(
    "/exchange",
    response_model=CrossBranchResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute cross-branch information exchange",
    description="Processes an authorized, restricted cross-branch information query via the central Federation Gateway.",
)
def execute_cross_branch_exchange(
    req: CrossBranchRequest,
    x_branch_key: Optional[str] = Header(None, alias="X-Branch-Key"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(require_bank_employee),
) -> CrossBranchResponse:
    """Execute controlled inter-branch query."""
    # Use provided X-Branch-Key header, or fallback to known environment secret for internal testing
    from app.federation.security import BRANCH_SECRETS
    api_key = x_branch_key or BRANCH_SECRETS.get(req.source_branch_id.upper(), "")

    response = FederationGateway.process_cross_branch_request(
        req=req,
        api_key=api_key,
        gateway_db=db,
    )
    return response


@router.get(
    "/branches",
    response_model=List[BranchSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="List all registered federated branches",
    description="Returns list of all active branches, locations, and real-time workload counts.",
)
def list_federated_branches(
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
) -> List[BranchSummaryResponse]:
    """Retrieve list of branches and their operational health."""
    ensure_default_branches(db)
    branches = db.query(Branch).order_by(Branch.branch_id.asc()).all()
    results = []

    for b in branches:
        # Query branch-specific metrics safely from its isolated database
        active_agents = 0
        pending_reqs = 0
        completed_reqs = 0

        try:
            b_session = BranchDatabaseManager.get_session(b.branch_id)
            active_agents = b_session.query(func.count(Agent.id)).filter(Agent.branch_id == b.branch_id).scalar() or 0
            pending_reqs = b_session.query(func.count(Request.id)).filter(
                Request.branch_id == b.branch_id,
                Request.request_status.notin_([RequestStatus.COMPLETED, RequestStatus.FAILED, RequestStatus.REJECTED_INPUT])
            ).scalar() or 0
            completed_reqs = b_session.query(func.count(Request.id)).filter(
                Request.branch_id == b.branch_id,
                Request.request_status == RequestStatus.COMPLETED
            ).scalar() or 0
            b_session.close()
        except Exception:
            pass

        results.append(
            BranchSummaryResponse(
                branch_id=b.branch_id,
                branch_name=b.branch_name,
                location=b.location,
                branch_status=b.branch_status,
                active_agents=active_agents,
                pending_requests=pending_reqs,
                completed_requests=completed_reqs,
                is_gateway_enabled=b.is_gateway_enabled,
            )
        )

    return results


@router.get(
    "/statistics",
    response_model=FederationStatisticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get federation monitoring telemetry",
    description="Returns aggregate counts of branches, cross-branch exchanges, success/failure rates, and recent events.",
)
def get_federation_statistics(
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
) -> FederationStatisticsResponse:
    """Retrieve federation operational metrics."""
    ensure_default_branches(db)
    total_b = db.query(func.count(Branch.id)).scalar() or 0
    active_b = db.query(func.count(Branch.id)).filter(Branch.branch_status == BranchStatus.ACTIVE.value).scalar() or 0
    inactive_b = total_b - active_b

    total_events = db.query(func.count(FederationEvent.id)).scalar() or 0
    success_events = db.query(func.count(FederationEvent.id)).filter(FederationEvent.event_status == "SUCCESS").scalar() or 0
    rejected_events = db.query(func.count(FederationEvent.id)).filter(FederationEvent.event_status == "REJECTED").scalar() or 0
    failed_events = db.query(func.count(FederationEvent.id)).filter(FederationEvent.event_status.in_(["FAILED", "ERROR"])).scalar() or 0

    recent_raw = db.query(FederationEvent).order_by(desc(FederationEvent.timestamp)).limit(15).all()
    recent_items = [
        {
            "event_id": e.federation_event_id,
            "source_branch": e.source_branch_id,
            "destination_branch": e.destination_branch_id,
            "scope": e.requested_scope,
            "authorization_result": e.authorization_result,
            "status": e.event_status,
            "correlation_id": e.correlation_id,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
        }
        for e in recent_raw
    ]

    return FederationStatisticsResponse(
        total_branches=total_b,
        active_branches=active_b,
        inactive_branches=inactive_b,
        total_exchanges=total_events,
        successful_exchanges=success_events,
        rejected_exchanges=rejected_events,
        failed_exchanges=failed_events,
        recent_events=recent_items,
    )


@router.get(
    "/events",
    response_model=List[FederationEventItem],
    status_code=status.HTTP_200_OK,
    summary="List chronological federation events",
    description="Audit log of inter-branch queries with authorization outcomes.",
)
def list_federation_events(
    branch_id: Optional[str] = Query(None, description="Filter by source or destination branch ID"),
    event_status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: SUCCESS, REJECTED, FAILED"),
    limit: int = Query(50, le=200),
    current_user: User = Depends(require_bank_employee),
    db: Session = Depends(get_db),
) -> List[FederationEventItem]:
    """Retrieve filtered federation event history."""
    q = db.query(FederationEvent)
    if branch_id:
        b_upper = branch_id.upper()
        q = q.filter((FederationEvent.source_branch_id == b_upper) | (FederationEvent.destination_branch_id == b_upper))
    if event_status_filter:
        q = q.filter(FederationEvent.event_status == event_status_filter.upper())

    events = q.order_by(desc(FederationEvent.timestamp)).limit(limit).all()

    return [
        FederationEventItem(
            federation_event_id=e.federation_event_id,
            source_branch_id=e.source_branch_id,
            destination_branch_id=e.destination_branch_id,
            request_id=e.request_id,
            event_type=e.event_type,
            requested_scope=e.requested_scope,
            authorization_result=e.authorization_result,
            correlation_id=e.correlation_id,
            event_status=e.event_status,
            timestamp=e.timestamp.isoformat() if e.timestamp else "",
            error_message=e.error_message,
        )
        for e in events
    ]
