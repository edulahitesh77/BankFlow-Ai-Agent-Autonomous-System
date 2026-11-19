"""
BankFlow AI - Standard Message Schema
Defines the authoritative Pydantic JSON message schema and event vocabulary for all agent communication.
"""

import enum
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel, Field, field_validator


class BankingEventType(str, enum.Enum):
    """Vocabulary of permitted multi-agent banking workflow events."""
    REQUEST_CREATED = "REQUEST_CREATED"
    REQUEST_CLASSIFIED = "REQUEST_CLASSIFIED"
    REQUEST_ASSIGNED = "REQUEST_ASSIGNED"
    REQUEST_ACCEPTED = "REQUEST_ACCEPTED"
    VERIFICATION_COMPLETED = "VERIFICATION_COMPLETED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
    REQUEST_NEEDS_CORRECTION = "REQUEST_NEEDS_CORRECTION"
    SERVICE_STARTED = "SERVICE_STARTED"
    SERVICE_COMPLETED = "SERVICE_COMPLETED"
    SERVICE_FAILED = "SERVICE_FAILED"
    AGENT_AVAILABLE = "AGENT_AVAILABLE"
    AGENT_UNAVAILABLE = "AGENT_UNAVAILABLE"
    AGENT_HEARTBEAT = "AGENT_HEARTBEAT"
    SUPERVISOR_ALERT = "SUPERVISOR_ALERT"


# Sensitive field keys forbidden from message payloads for security compliance
FORBIDDEN_SENSITIVE_KEYS = {
    "password",
    "password_hash",
    "token",
    "access_token",
    "jwt",
    "authorization",
    "secret",
}


class StandardBankingMessage(BaseModel):
    """
    Authoritative standard message envelope for all multi-agent broker communication.
    Every message exchanged across RabbitMQ queues must strictly adhere to this schema.
    """
    message_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique UUID identifying this specific message instance.",
    )
    request_id: str = Field(
        ...,
        min_length=3,
        max_length=60,
        description="Authoritative customer service request ID (e.g. BFA-REQ-2026-00001).",
    )
    request_version: int = Field(
        default=0,
        ge=0,
        description="Monotonically increasing request assignment version to prevent stale transitions.",
    )
    sender_agent_id: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Identifier of the publishing agent (e.g. AGT-INTAKE-01, RequestAgent_1).",
    )
    receiver_agent_id: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Intended recipient agent or pool (e.g. RequestAgentPool, AGT-VERIF-01).",
    )
    event_type: BankingEventType = Field(
        ...,
        description="Standardized event vocabulary tag.",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="ISO-8601 UTC timestamp of message emission.",
    )
    correlation_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Workflow correlation ID for end-to-end distributed tracing.",
    )
    payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="Contextual event payload (strictly non-sensitive).",
    )
    reason_code: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Structured rationale for exception or routing decisions.",
    )
    retry_count: int = Field(
        default=0,
        ge=0,
        description="Number of times this message has been retried.",
    )

    @field_validator("payload")
    @classmethod
    def validate_payload_security(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Ensures sensitive authentication data is never transmitted across message broker."""
        if not isinstance(v, dict):
            raise ValueError("Message payload must be a JSON object dictionary.")

        def sanitize(obj: Any) -> Any:
            if isinstance(obj, dict):
                clean = {}
                for k, val in obj.items():
                    if str(k).lower() in FORBIDDEN_SENSITIVE_KEYS:
                        raise ValueError(f"Forbidden sensitive credential field '{k}' detected in message payload.")
                    clean[k] = sanitize(val)
                return clean
            elif isinstance(obj, list):
                return [sanitize(item) for item in obj]
            return obj

        return sanitize(v)

    def to_json_dict(self) -> Dict[str, Any]:
        """Serializes message to a JSON-compatible dictionary."""
        data = self.model_dump()
        data["timestamp"] = self.timestamp.isoformat()
        data["event_type"] = self.event_type.value if hasattr(self.event_type, "value") else str(self.event_type)
        return data
