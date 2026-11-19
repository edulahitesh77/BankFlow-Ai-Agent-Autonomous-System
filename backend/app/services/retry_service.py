"""
BankFlow AI - Recovery Retry Policy Service (Phase 8)
Implements configurable exponential backoff, retryable classification,
and human-review escalation upon retry exhaustion.
"""

import logging
import math
from typing import Dict, Any, Optional, Union
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.config import settings
from app.models.request import Request, RequestStatus
from app.models.failure_record import AgentFailure, RecoveryStatus
from app.services.audit_service import AuditService

logger = logging.getLogger("bankflow_ai.services.retry")

# Explicit patterns that must NOT be automatically retried (deterministic business rule violations)
NON_RETRYABLE_PATTERNS = [
    "invalid leaf count",
    "leaves must be",
    "account closed",
    "account suspended",
    "account not found",
    "ownership mismatch",
    "malformed payload",
    "schema violation",
    "invalid service type",
    "duplicate completion",
    "customer cannot use another",
]


class RecoveryRetryService:
    """
    Manages retry limits, exponential backoff computation, error classification,
    and fallback escalation to human review.
    """

    @staticmethod
    def calculate_backoff_delay(attempt: int) -> float:
        """
        Calculates exponential backoff delay for a given retry attempt.
        Formula: initial_delay * (backoff_factor ** (attempt - 1)), bounded by max_delay.
        Attempt 1: 2.0s
        Attempt 2: 4.0s
        Attempt 3: 8.0s
        """
        if attempt <= 0:
            return 0.0

        delay = settings.RECOVERY_INITIAL_RETRY_DELAY_SECONDS * (
            settings.RECOVERY_BACKOFF_FACTOR ** (attempt - 1)
        )
        return min(delay, settings.RECOVERY_MAX_RETRY_DELAY_SECONDS)

    @staticmethod
    def is_retryable_error(error: Union[Exception, str]) -> bool:
        """
        Classifies whether an error is transient (retryable) or permanent (non-retryable).
        Transient errors: timeouts, agent crashes, broker blips, transient locks.
        Permanent errors: invalid input fields, business rule failures, closed accounts.
        """
        err_str = str(error).lower()
        for pattern in NON_RETRYABLE_PATTERNS:
            if pattern in err_str:
                return False
        return True

    @staticmethod
    def can_retry_request(
        request: Request,
        error: Optional[Union[Exception, str]] = None,
    ) -> bool:
        """
        Determines if a request has remaining retry quota and the error is retryable.
        """
        if request.retry_count >= settings.RECOVERY_MAX_RETRIES:
            return False

        if error is not None and not RecoveryRetryService.is_retryable_error(error):
            return False

        return True

    @staticmethod
    def escalate_to_human_intervention(
        db: Session,
        request: Request,
        failure_record: Optional[AgentFailure] = None,
        reason: str = "Max recovery retries exhausted",
        user_id: Optional[int] = None,
    ) -> Request:
        """
        Safely transitions an unrecoverable request into HUMAN_REVIEW without losing data.
        Records audit trail and updates failure registry.
        """
        previous_status = request.request_status.value if hasattr(request.request_status, "value") else str(request.request_status)
        request.request_status = RequestStatus.HUMAN_REVIEW
        request.review_required = True
        request.reason_code = "RECOVERY_RETRIES_EXHAUSTED"
        request.recovery_reason = reason[:255]
        request.last_recovery_at = datetime.now(timezone.utc)

        # Unassign from failed agent
        request.assigned_agent_id = None
        request.assignment_version += 1

        if failure_record:
            failure_record.recovery_status = RecoveryStatus.ESCALATED_TO_HUMAN.value
            failure_record.recovered_at = datetime.now(timezone.utc)

        AuditService.record_event(
            db=db,
            action="REQUEST_ESCALATED_TO_HUMAN_REVIEW",
            outcome="SUCCESS",
            user_id=user_id,
            request_id=request.request_id,
            description=f"Request {request.request_id} escalated to HUMAN_REVIEW after exceeding retry limit ({settings.RECOVERY_MAX_RETRIES}). Reason: {reason}",
        )

        db.commit()
        logger.warning(
            "Request '%s' escalated to HUMAN_REVIEW (Previous: %s, Retries: %s)",
            request.request_id,
            previous_status,
            request.retry_count,
        )
        return request
