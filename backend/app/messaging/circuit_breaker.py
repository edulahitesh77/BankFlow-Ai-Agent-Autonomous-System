"""
BankFlow AI - Circuit Breaker for External Dependencies
Provides stateful circuit protection (CLOSED, OPEN, HALF_OPEN) for RabbitMQ
and external integrations to prevent cascade failures.
"""

import enum
import logging
import threading
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Callable

from app.config import settings

logger = logging.getLogger("bankflow_ai.messaging.circuit_breaker")


class CircuitBreakerState(str, enum.Enum):
    """Operational states of the circuit breaker."""
    CLOSED = "CLOSED"        # Normal operations, all traffic allowed
    OPEN = "OPEN"            # Dependency unavailable, calls rejected or routed to fallback
    HALF_OPEN = "HALF_OPEN"  # Testing dependency recovery with limited canary requests


class CircuitBreakerOpenException(Exception):
    """Raised when an operation is attempted while the circuit is in the OPEN state."""
    pass


class CircuitBreaker:
    """
    Thread-safe circuit breaker protecting services against failing dependencies.
    """

    def __init__(
        self,
        name: str = "RabbitMQBroker",
        failure_threshold: Optional[int] = None,
        recovery_timeout_seconds: Optional[float] = None,
        half_open_max_requests: Optional[int] = None,
    ):
        self.name = name
        self.failure_threshold = (
            failure_threshold
            if failure_threshold is not None
            else settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD
        )
        self.recovery_timeout_seconds = (
            recovery_timeout_seconds
            if recovery_timeout_seconds is not None
            else settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT_SECONDS
        )
        self.half_open_max_requests = (
            half_open_max_requests
            if half_open_max_requests is not None
            else settings.CIRCUIT_BREAKER_HALF_OPEN_MAX_REQUESTS
        )

        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_attempts = 0
        self._last_state_change = datetime.now(timezone.utc)
        self._last_failure_time: Optional[datetime] = None
        self._last_error_message: Optional[str] = None
        self._lock = threading.RLock()

    @property
    def state(self) -> CircuitBreakerState:
        with self._lock:
            # Check for automatic transition from OPEN to HALF_OPEN after timeout
            if self._state == CircuitBreakerState.OPEN:
                elapsed = (datetime.now(timezone.utc) - self._last_state_change).total_seconds()
                if elapsed >= self.recovery_timeout_seconds:
                    self._transition_to(
                        CircuitBreakerState.HALF_OPEN,
                        reason=f"Recovery timeout ({self.recovery_timeout_seconds}s) elapsed; canary trial started",
                    )
            return self._state

    def _transition_to(self, new_state: CircuitBreakerState, reason: str = "") -> None:
        """Internal helper to transition states with structured logging."""
        old_state = self._state
        self._state = new_state
        self._last_state_change = datetime.now(timezone.utc)
        if new_state == CircuitBreakerState.CLOSED:
            self._failure_count = 0
            self._success_count = 0
            self._half_open_attempts = 0
        elif new_state == CircuitBreakerState.HALF_OPEN:
            self._half_open_attempts = 0
            self._success_count = 0
        elif new_state == CircuitBreakerState.OPEN:
            self._half_open_attempts = 0

        logger.warning(
            "CircuitBreaker [%s] transitioned from %s to %s. Reason: %s",
            self.name,
            old_state.value,
            new_state.value,
            reason,
        )

    def can_execute(self) -> bool:
        """Determines whether a call to the dependency is allowed."""
        with self._lock:
            current_state = self.state
            if current_state == CircuitBreakerState.CLOSED:
                return True
            elif current_state == CircuitBreakerState.HALF_OPEN:
                if self._half_open_attempts < self.half_open_max_requests:
                    self._half_open_attempts += 1
                    return True
                return False
            else:  # OPEN
                return False

    def record_success(self) -> None:
        """Records a successful operation against the dependency."""
        with self._lock:
            if self._state == CircuitBreakerState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.half_open_max_requests:
                    self._transition_to(
                        CircuitBreakerState.CLOSED,
                        reason=f"Canary test succeeded ({self._success_count} consecutive successful requests)",
                    )
            elif self._state == CircuitBreakerState.CLOSED:
                self._failure_count = 0

    def record_failure(self, error: Optional[Exception] = None) -> None:
        """Records a failure when interacting with the dependency."""
        with self._lock:
            self._failure_count += 1
            now = datetime.now(timezone.utc)
            self._last_failure_time = now
            if error:
                self._last_error_message = str(error)

            if self._state == CircuitBreakerState.HALF_OPEN:
                self._transition_to(
                    CircuitBreakerState.OPEN,
                    reason=f"Canary call failed: {error or 'Unknown error'}",
                )
            elif self._state == CircuitBreakerState.CLOSED:
                if self._failure_count >= self.failure_threshold:
                    self._transition_to(
                        CircuitBreakerState.OPEN,
                        reason=f"Consecutive failures ({self._failure_count}) exceeded threshold ({self.failure_threshold})",
                    )

    def trip(self, reason: str = "Manual or simulated trip") -> None:
        """Forces the circuit breaker into the OPEN state."""
        with self._lock:
            self._transition_to(CircuitBreakerState.OPEN, reason=reason)

    def reset(self, reason: str = "Manual or simulated reset") -> None:
        """Forces the circuit breaker back to the CLOSED state."""
        with self._lock:
            self._transition_to(CircuitBreakerState.CLOSED, reason=reason)

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Executes a callable protected by the circuit breaker."""
        if not self.can_execute():
            raise CircuitBreakerOpenException(
                f"Circuit breaker '{self.name}' is OPEN. Operation rejected to protect dependency."
            )
        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure(e)
            raise

    def get_status(self) -> Dict[str, Any]:
        """Returns structured health snapshot of the circuit breaker."""
        with self._lock:
            current_state = self.state
            return {
                "name": self.name,
                "state": current_state.value,
                "failure_count": self._failure_count,
                "failure_threshold": self.failure_threshold,
                "recovery_timeout_seconds": self.recovery_timeout_seconds,
                "half_open_attempts": self._half_open_attempts,
                "half_open_max_requests": self.half_open_max_requests,
                "last_state_change": self._last_state_change.isoformat() if self._last_state_change else None,
                "last_failure_time": self._last_failure_time.isoformat() if self._last_failure_time else None,
                "last_error_message": self._last_error_message,
            }


# Singleton circuit breaker instance for RabbitMQ communication
rabbitmq_circuit_breaker = CircuitBreaker("RabbitMQBroker")
