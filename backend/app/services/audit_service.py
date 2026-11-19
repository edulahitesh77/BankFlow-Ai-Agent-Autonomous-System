"""
BankFlow AI - Centralized Audit Logging Service
Provides tamper-resistant logging of all authentication events, banking requests,
agent assignments, supervisor reviews, and administrative role actions.
Ensures zero storage of plain-text passwords, tokens, or encryption keys in audit records.
"""

import re
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.audit_log import AuditLog

FORBIDDEN_AUDIT_PATTERNS = [
    re.compile(r"eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)?", re.IGNORECASE),
    re.compile(r"(bearer\s+token|bearer|jwt|token)[\s:=]+([^\s,;]+)", re.IGNORECASE),
    re.compile(r"(password|passwd|pwd)[\s:=]+([^\s,;]+)", re.IGNORECASE),
    re.compile(r"(secret|key|encryption_key)[\s:=]+([^\s,;]+)", re.IGNORECASE),
    re.compile(r"(pin|cvv|pan)[\s:=]+([^\s,;]+)", re.IGNORECASE),
    re.compile(r"\$argon2id\$[^\s,;]+", re.IGNORECASE),
]


class AuditService:
    """Service handling audit trail emission, sanitization, and compliance queries."""

    @staticmethod
    def sanitize_description(text: Optional[str]) -> Optional[str]:
        """
        Scans audit descriptions to sanitize any leaked passwords, JWT tokens,
        Argon2id hashes, or encryption keys before committing to the database.
        """
        if not text:
            return text

        sanitized = text
        for pattern in FORBIDDEN_AUDIT_PATTERNS:
            if pattern.groups >= 1:
                sanitized = pattern.sub(r"\1=[REDACTED_BY_SECURITY_POLICY]", sanitized)
            else:
                sanitized = pattern.sub("[REDACTED_BY_SECURITY_POLICY]", sanitized)

        return sanitized

    @classmethod
    def record_event(
        cls,
        db: Session,
        action: str,
        user_id: Optional[int] = None,
        request_id: Optional[str] = None,
        outcome: str = "SUCCESS",
        description: Optional[str] = None,
        source_ip: Optional[str] = None,
        entity_type: str = "SECURITY",
        entity_id: Optional[str] = None,
        auto_commit: bool = True,
    ) -> AuditLog:
        """
        Creates and persists an immutable audit record conforming to Phase 7 requirements.
        """
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y%m%d")
        event_id = f"AUD-{date_str}-{uuid.uuid4().hex[:8].upper()}"

        clean_description = cls.sanitize_description(description)

        audit_entry = AuditLog(
            event_id=event_id,
            user_id=user_id,
            request_id=request_id,
            action=action.upper(),
            outcome=outcome.upper(),
            entity_type=entity_type.upper(),
            entity_id=entity_id or request_id or str(user_id or "SYSTEM"),
            description=clean_description,
            source_ip=source_ip or "127.0.0.1",
        )

        db.add(audit_entry)
        if auto_commit:
            try:
                db.commit()
                db.refresh(audit_entry)
            except Exception:
                db.rollback()
                raise

        return audit_entry

    @classmethod
    def get_audit_trail(
        cls,
        db: Session,
        action: Optional[str] = None,
        request_id: Optional[str] = None,
        user_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """Returns paginated audit records for authorized bank staff inspection."""
        query = db.query(AuditLog)

        if action:
            query = query.filter(AuditLog.action == action.upper())
        if request_id:
            query = query.filter(AuditLog.request_id == request_id)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)

        total = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(desc(AuditLog.timestamp)).offset(offset).limit(page_size).all()

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items,
        }
