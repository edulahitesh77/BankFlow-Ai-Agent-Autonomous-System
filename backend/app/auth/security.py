"""
BankFlow AI - Authentication Security Module
Handles Argon2id password hashing, strength validation, and login rate limiting.
"""

import re
import time
from collections import defaultdict
from typing import Tuple, Dict, List
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from app.config import settings

# Initialize Argon2id password hasher with secure defaults
_ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,  # 64 MB
    parallelism=4,
    hash_len=32,
    salt_len=16,
)


def hash_password(plain_password: str) -> str:
    """Hash a plain text password using Argon2id."""
    return _ph.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against an Argon2id hash.
    Safely returns False if hash is invalid or password does not match.
    """
    if not hashed_password:
        return False
    try:
        return _ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate that a password meets banking complexity requirements:
    - At least 8 characters in length
    - At least one uppercase letter (A-Z)
    - At least one lowercase letter (a-z)
    - At least one numeric digit (0-9)
    - At least one special character (!@#$%^&*()-_=+[]{}|;:,.<>?)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one numeric digit."
    if not re.search(r"[!@#$%^&*()\-_=+\[\]{}|;:,.<>?/~`]", password):
        return False, "Password must contain at least one special character."
    return True, ""


# ---------------------------------------------------------------------------
# Rate Limiting for Authentication Attempts
# Protects against brute-force attacks and credential stuffing
# ---------------------------------------------------------------------------

class RateLimiter:
    """In-memory rate limiter tracking failed login attempts per key."""

    def __init__(self, max_attempts: int, window_seconds: int):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        # key -> list of failure timestamps
        self._failures: Dict[str, List[float]] = defaultdict(list)

    def _cleanup(self, key: str, now: float) -> None:
        """Remove timestamps older than the rate limit window."""
        cutoff = now - self.window_seconds
        self._failures[key] = [t for t in self._failures[key] if t > cutoff]

    def is_rate_limited(self, key: str) -> Tuple[bool, int]:
        """
        Check if an identifier is rate-limited.
        Returns (is_limited, retry_after_seconds).
        """
        now = time.time()
        self._cleanup(key, now)
        failures = self._failures[key]
        if len(failures) >= self.max_attempts:
            oldest_failure = failures[0]
            retry_after = int(self.window_seconds - (now - oldest_failure)) + 1
            return True, max(1, retry_after)
        return False, 0

    def record_failure(self, key: str) -> None:
        """Record a failed authentication attempt."""
        now = time.time()
        self._cleanup(key, now)
        self._failures[key].append(now)

    def record_success(self, key: str) -> None:
        """Clear failures on successful login."""
        if key in self._failures:
            del self._failures[key]

    def reset_all(self) -> None:
        """Reset rate limiter state (used in testing)."""
        self._failures.clear()


# Global rate limiter instance
login_rate_limiter = RateLimiter(
    max_attempts=settings.RATE_LIMIT_LOGIN_MAX_ATTEMPTS,
    window_seconds=settings.RATE_LIMIT_LOGIN_WINDOW_SECONDS,
)
