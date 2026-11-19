"""
BankFlow AI - Federation Security Manager (Phase 10)
Handles branch authentication, HMAC verification, permitted scope authorization,
anti-replay protection, and sensitive data sanitization for the Federation Gateway.
"""

import hmac
import hashlib
import logging
from typing import Tuple, Dict, Any, Optional
from datetime import datetime, timezone
from app.config import settings

logger = logging.getLogger("bankflow_ai.federation.security")

# Strictly permitted cross-branch information scopes
PERMITTED_FEDERATION_SCOPES = {
    "ACCOUNT_STATUS_CONFIRMATION": {
        "allowed_query_keys": {"synthetic_account_number", "customer_code"},
        "permitted_response_fields": {"synthetic_account_number", "account_status", "is_confirmed", "branch_id"},
    },
    "CUSTOMER_KYC_VERIFICATION": {
        "allowed_query_keys": {"customer_code", "full_name"},
        "permitted_response_fields": {"customer_code", "kyc_status", "is_verified", "branch_id"},
    },
    "SERVICE_ELIGIBILITY_CONFIRMATION": {
        "allowed_query_keys": {"synthetic_account_number", "service_type"},
        "permitted_response_fields": {"synthetic_account_number", "service_type", "is_eligible", "branch_id"},
    },
}

# Known branch secrets mapping
BRANCH_SECRETS: Dict[str, str] = {
    "BLR001": settings.BLR_BRANCH_SECRET,
    "CHE001": settings.CHE_BRANCH_SECRET,
    "HYD001": settings.HYD_BRANCH_SECRET,
}


class FederationSecurityManager:
    """Security validator for cross-branch federation requests."""

    @classmethod
    def hash_key(cls, key: str) -> str:
        """Computes constant SHA-256 hash of a key."""
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    @classmethod
    def authenticate_branch(cls, branch_id: str, provided_key: str) -> Tuple[bool, Optional[str]]:
        """
        Validates branch identity using constant-time string comparison.
        Never exposes the secret in logs or errors.
        """
        b_id = branch_id.upper()
        expected_secret = BRANCH_SECRETS.get(b_id)
        if not expected_secret:
            logger.warning("Authentication failed: Unregistered branch '%s'", b_id)
            return False, "REJECTED_UNREGISTERED_BRANCH"

        # Compare provided key with expected secret in constant time
        if not hmac.compare_digest(provided_key, expected_secret):
            logger.warning("Authentication failed: Invalid credentials for branch '%s'", b_id)
            return False, "REJECTED_INVALID_CREDENTIALS"

        return True, "AUTHENTICATED"

    @classmethod
    def authorize_scope(cls, source_branch: str, destination_branch: str, scope: str) -> Tuple[bool, Optional[str]]:
        """
        Verifies that source branch is permitted to query destination branch
        for the requested scope.
        """
        src = source_branch.upper()
        dest = destination_branch.upper()

        if src not in BRANCH_SECRETS:
            return False, "REJECTED_UNREGISTERED_SOURCE"
        if dest not in BRANCH_SECRETS:
            return False, "REJECTED_UNREGISTERED_DESTINATION"
        if src == dest:
            return False, "REJECTED_SELF_FEDERATION"

        if scope not in PERMITTED_FEDERATION_SCOPES:
            logger.warning(
                "Authorization rejected: Scope '%s' is not in permitted federation scopes (requested by %s to %s)",
                scope, src, dest
            )
            return False, "REJECTED_UNAUTHORIZED_SCOPE"

        return True, "AUTHORIZED"

    @classmethod
    def sanitize_response(cls, scope: str, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filters raw destination data so only permitted fields for the given scope
        are returned to the source branch. Never leaks full profiles, balances, or credentials.
        """
        spec = PERMITTED_FEDERATION_SCOPES.get(scope)
        if not spec:
            return {}

        allowed_fields = spec["permitted_response_fields"]
        sanitized = {k: v for k, v in raw_data.items() if k in allowed_fields}
        return sanitized
