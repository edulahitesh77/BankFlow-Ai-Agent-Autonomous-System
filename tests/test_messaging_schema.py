"""
BankFlow AI - Message Schema Test Suite
Tests validation of standard JSON banking messages, event vocabulary,
payload security sanitization, and version constraints.
"""

import sys
import os
import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.messaging.message_schema import (
    StandardBankingMessage,
    BankingEventType,
    FORBIDDEN_SENSITIVE_KEYS,
)


def test_valid_banking_message_accepted():
    """Verify that a properly constructed standard banking message passes validation."""
    msg = StandardBankingMessage(
        request_id="BFA-REQ-2026-00001",
        request_version=1,
        sender_agent_id="AGT-INTAKE-01",
        receiver_agent_id="RequestAgentPool",
        event_type=BankingEventType.REQUEST_CLASSIFIED,
        payload={"service_type": "CHEQUE_BOOK", "leaves": 50},
        reason_code="VALID_INPUT",
    )

    assert msg.message_id is not None
    assert len(msg.message_id) > 10
    assert msg.request_id == "BFA-REQ-2026-00001"
    assert msg.request_version == 1
    assert msg.event_type == BankingEventType.REQUEST_CLASSIFIED
    assert msg.payload["leaves"] == 50
    assert msg.reason_code == "VALID_INPUT"

    # Test serialization
    data = msg.to_json_dict()
    assert isinstance(data, dict)
    assert data["event_type"] == "REQUEST_CLASSIFIED"
    assert "timestamp" in data


def test_missing_required_fields_rejected():
    """Verify that omitting required message schema fields raises a ValidationError."""
    # Missing request_id
    with pytest.raises(ValidationError):
        StandardBankingMessage(
            sender_agent_id="AGT-INTAKE-01",
            receiver_agent_id="RequestAgentPool",
            event_type=BankingEventType.REQUEST_CLASSIFIED,
        )

    # Missing event_type
    with pytest.raises(ValidationError):
        StandardBankingMessage(
            request_id="BFA-REQ-2026-00001",
            sender_agent_id="AGT-INTAKE-01",
            receiver_agent_id="RequestAgentPool",
        )


def test_invalid_event_type_rejected():
    """Verify that arbitrary string events not in BankingEventType are rejected."""
    with pytest.raises(ValidationError):
        StandardBankingMessage(
            request_id="BFA-REQ-2026-00001",
            sender_agent_id="AGT-INTAKE-01",
            receiver_agent_id="RequestAgentPool",
            event_type="UNAUTHORIZED_CUSTOM_EVENT",
        )


def test_negative_request_version_rejected():
    """Verify request version cannot be negative."""
    with pytest.raises(ValidationError):
        StandardBankingMessage(
            request_id="BFA-REQ-2026-00001",
            request_version=-1,
            sender_agent_id="AGT-INTAKE-01",
            receiver_agent_id="RequestAgentPool",
            event_type=BankingEventType.REQUEST_CLASSIFIED,
        )


def test_forbidden_sensitive_credentials_rejected_in_payload():
    """Verify that payloads containing sensitive authentication information are strictly rejected."""
    for sensitive_key in ["password", "password_hash", "token", "access_token", "jwt", "secret"]:
        with pytest.raises(ValidationError) as excinfo:
            StandardBankingMessage(
                request_id="BFA-REQ-2026-00001",
                sender_agent_id="AGT-CUST-01",
                receiver_agent_id="AGT-INTAKE-01",
                event_type=BankingEventType.REQUEST_CREATED,
                payload={"user_id": 10, sensitive_key: "leaked_secret_val"},
            )
        assert f"Forbidden sensitive credential field '{sensitive_key}'" in str(excinfo.value)
