"""
BankFlow AI - Request State Machine
Implements strict, auditable lifecycle transitions for banking service requests.
Enforces explicit rules, prevents duplicate completions, and validates allowed transitions.
"""

from typing import Optional, Dict, Set
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from app.models.request import Request, RequestStatus
from app.models.audit_log import AuditLog


class StateMachineError(Exception):
    """Base exception for state machine violations."""
    pass


class InvalidStateTransitionError(StateMachineError):
    """Raised when an illegal state transition is attempted."""
    pass


class DuplicateCompletionError(StateMachineError):
    """Raised when a request is already completed and cannot be transitioned again."""
    pass


# Strict lifecycle transition matrix
VALID_TRANSITIONS: Dict[RequestStatus, Set[RequestStatus]] = {
    RequestStatus.NEW: {
        RequestStatus.CLASSIFIED,
        RequestStatus.NEEDS_CORRECTION,
        RequestStatus.REJECTED_INPUT,
        RequestStatus.HUMAN_REVIEW,
    },
    RequestStatus.CLASSIFIED: {
        RequestStatus.QUEUED,
        RequestStatus.NEEDS_CORRECTION,
        RequestStatus.HUMAN_REVIEW,
        RequestStatus.REJECTED_INPUT,
    },
    RequestStatus.QUEUED: {
        RequestStatus.VERIFIED,
        RequestStatus.IN_SERVICE,
        RequestStatus.HUMAN_REVIEW,
        RequestStatus.NEEDS_CORRECTION,
        RequestStatus.REJECTED_INPUT,
    },
    RequestStatus.VERIFIED: {
        RequestStatus.IN_SERVICE,
        RequestStatus.HUMAN_REVIEW,
        RequestStatus.NEEDS_CORRECTION,
        RequestStatus.REJECTED_INPUT,
        RequestStatus.COMPLETED,
    },
    RequestStatus.IN_SERVICE: {
        RequestStatus.COMPLETED,
        RequestStatus.FAILED,
        RequestStatus.HUMAN_REVIEW,
        RequestStatus.NEEDS_CORRECTION,
    },
    RequestStatus.NEEDS_CORRECTION: {
        RequestStatus.NEW,  # Customer resubmission
    },
    RequestStatus.HUMAN_REVIEW: {
        RequestStatus.VERIFIED,       # Concurrence / cleared by supervisor
        RequestStatus.QUEUED,         # Re-queued for agent dispatch
        RequestStatus.NEEDS_CORRECTION, # Additional info requested
        RequestStatus.REJECTED_INPUT, # Supervisor rejected
    },
    RequestStatus.REJECTED_INPUT: set(),  # Terminal state
    RequestStatus.COMPLETED: set(),       # Terminal state: duplicate completion forbidden
    RequestStatus.FAILED: {
        RequestStatus.QUEUED,         # Recovered retry
        RequestStatus.NEEDS_CORRECTION,
    },
}


def can_transition(current_status: RequestStatus, target_status: RequestStatus) -> bool:
    """Checks whether the requested state transition is legally permissible."""
    allowed = VALID_TRANSITIONS.get(current_status, set())
    return target_status in allowed


def transition_request(
    db: Session,
    request: Request,
    new_status: RequestStatus,
    agent_code: str,
    reason_code: Optional[str] = None,
    note: Optional[str] = None,
    user_id: Optional[int] = None,
) -> Request:
    """
    Executes a validated lifecycle transition on a customer service request.
    Records timestamp, updates reason codes, and generates compliance audit trails.
    """
    current_status = request.request_status

    if current_status == RequestStatus.COMPLETED:
        raise DuplicateCompletionError(
            f"Request '{request.request_id}' is already in terminal COMPLETED state. Cannot transition to '{new_status}'."
        )

    if not can_transition(current_status, new_status):
        raise InvalidStateTransitionError(
            f"Illegal state transition for '{request.request_id}': cannot move from '{current_status}' to '{new_status}'."
        )

    # Apply state change
    old_status_val = current_status.value if hasattr(current_status, "value") else str(current_status)
    new_status_val = new_status.value if hasattr(new_status, "value") else str(new_status)

    request.request_status = new_status
    if reason_code:
        request.reason_code = reason_code

    if new_status == RequestStatus.COMPLETED:
        request.completed_at = func.now()

    # Record Audit Log
    desc = f"Transitioned from {old_status_val} to {new_status_val} by agent '{agent_code}'."
    if reason_code:
        desc += f" Reason Code: {reason_code}."
    if note:
        desc += f" Note: {note}"

    from app.services.audit_service import AuditService

    AuditService.record_event(
        db=db,
        action="STATE_TRANSITION",
        user_id=user_id,
        request_id=request.request_id,
        outcome="SUCCESS",
        description=desc,
        source_ip="127.0.0.1",
        entity_type="REQUEST",
        entity_id=request.request_id,
        auto_commit=False,
    )
    db.flush()

    return request
