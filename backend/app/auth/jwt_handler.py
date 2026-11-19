"""
BankFlow AI - JWT Token Management Module
Handles JWT generation, claims encoding, verification, and revocation.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Set
import jwt
from fastapi import HTTPException, status
from app.config import settings

# In-memory revocation set tracking revoked token JTIs or signatures
_revoked_token_jtis: Set[str] = set()


def create_access_token(
    user_id: int,
    role: str,
    username: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Generate a signed JWT access token containing identity claims.
    Never includes password hashes or sensitive internal secrets.
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    jti = str(uuid.uuid4())
    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "type": "access",
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    encoded_jwt = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT access token.
    Raises HTTPException(401) on expiration, invalid signature, or revoked status.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    expired_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Access token has expired",
        headers={"WWW-Authenticate": "Bearer"},
    )
    revoked_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token has been revoked",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        jti = payload.get("jti")
        if jti and jti in _revoked_token_jtis:
            raise revoked_exception

        token_type = payload.get("type")
        if token_type != "access":
            raise credentials_exception

        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        return payload

    except jwt.ExpiredSignatureError:
        raise expired_exception
    except jwt.PyJWTError:
        raise credentials_exception


def revoke_token(token: str) -> None:
    """
    Revoke a token by adding its jti claim to the revocation registry.
    Ensures immediate server-side invalidation upon logout.
    """
    try:
        # Decode without verification to extract jti even if near expiration
        unverified_payload = jwt.decode(
            token,
            options={"verify_signature": False, "verify_exp": False},
        )
        jti = unverified_payload.get("jti")
        if jti:
            _revoked_token_jtis.add(jti)
    except Exception:
        # If token cannot even be decoded, nothing to revoke
        pass


def is_token_revoked(token: str) -> bool:
    """Check whether a token's jti is in the revoked set."""
    try:
        unverified_payload = jwt.decode(
            token,
            options={"verify_signature": False, "verify_exp": False},
        )
        jti = unverified_payload.get("jti")
        return bool(jti and jti in _revoked_token_jtis)
    except Exception:
        return True


def clear_revoked_tokens() -> None:
    """Clear revocation store (useful in test suites)."""
    _revoked_token_jtis.clear()
