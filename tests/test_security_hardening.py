"""
BankFlow AI - Phase 7 Security Hardening Test Suite
Verifies comprehensive protection across credentials, AES-256-GCM encryption,
RBAC privileges, JWT integrity, audit sanitization, and messaging safety.
"""

import sys
import os
import uuid
import pytest
from datetime import timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Ensure backend directory is in sys.path
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.main import app
from app.config import settings, validate_security_config
from app.database import Base, get_db
from app.models.user import User, UserRole
from app.models.customer import Customer
from app.models.employee import Employee
from app.models.account import Account
from app.models.request import Request, ServiceType, RequestStatus
from app.models.audit_log import AuditLog
from app.auth.security import (
    hash_password,
    verify_password,
    validate_password_strength,
    login_rate_limiter,
)
from app.auth.jwt_handler import (
    create_access_token,
    decode_access_token,
    revoke_token,
    clear_revoked_tokens,
)
from app.auth.encryption import (
    encrypt_field,
    decrypt_field,
    encrypt_payload_fields,
    decrypt_payload_fields,
    get_encryption_key,
    DecryptionError,
    ENCRYPTION_PREFIX,
)
from app.services.audit_service import AuditService
from app.messaging.message_schema import StandardBankingMessage, BankingEventType


@pytest.fixture(scope="function")
def client(db_session: Session) -> TestClient:
    """Configures TestClient wired to the isolated transactional database session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    login_rate_limiter.reset_all()
    clear_revoked_tokens()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def security_users(db_session: Session):
    """Provisions identities across all 4 roles: CUSTOMER, BANK_EMPLOYEE, SUPERVISOR, ADMINISTRATOR."""
    # 1. Customer A
    user_cust_a = User(
        username="sec_cust_a",
        email="sec_cust_a@bankflow.synthetic",
        password_hash=hash_password("Customer@2026!"),
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db_session.add(user_cust_a)
    db_session.flush()

    cust_a = Customer(
        user_id=user_cust_a.id,
        customer_code="CUST-SEC-001",
        full_name="Alice Customer",
        phone="+1-555-0101",
        email=user_cust_a.email,
        branch_id="BR-MAIN-01",
    )
    db_session.add(cust_a)
    db_session.flush()

    acc_a = Account(
        customer_id=cust_a.id,
        synthetic_account_number="ACC-SEC-001",
        account_type="SAVINGS",
        account_status="ACTIVE",
        branch_id="BR-MAIN-01",
    )
    db_session.add(acc_a)
    db_session.flush()

    # 2. Customer B
    user_cust_b = User(
        username="sec_cust_b",
        email="sec_cust_b@bankflow.synthetic",
        password_hash=hash_password("Customer@2026!"),
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db_session.add(user_cust_b)
    db_session.flush()

    cust_b = Customer(
        user_id=user_cust_b.id,
        customer_code="CUST-SEC-002",
        full_name="Bob Customer",
        phone="+1-555-0102",
        email=user_cust_b.email,
        branch_id="BR-MAIN-01",
    )
    db_session.add(cust_b)
    db_session.flush()

    # 3. Bank Employee (Regular Officer)
    user_emp = User(
        username="sec_employee",
        email="sec_emp@bankflow.synthetic",
        password_hash=hash_password("Employee@2026!"),
        role=UserRole.BANK_EMPLOYEE,
        is_active=True,
    )
    db_session.add(user_emp)
    db_session.flush()

    emp = Employee(
        user_id=user_emp.id,
        employee_code="EMP-SEC-001",
        full_name="Officer Charlie",
        department="Operations",
        designation="Bank Officer",
        branch_id="BR-MAIN-01",
    )
    db_session.add(emp)
    db_session.flush()

    # 4. Supervisor
    user_sup = User(
        username="sec_supervisor",
        email="sec_sup@bankflow.synthetic",
        password_hash=hash_password("Supervisor@2026!"),
        role=UserRole.SUPERVISOR,
        is_active=True,
    )
    db_session.add(user_sup)
    db_session.flush()

    sup = Employee(
        user_id=user_sup.id,
        employee_code="SUP-SEC-001",
        full_name="Supervisor Dana",
        department="Risk & Oversight",
        designation="Operations Supervisor",
        branch_id="BR-MAIN-01",
    )
    db_session.add(sup)
    db_session.flush()

    # 5. Administrator
    user_adm = User(
        username="sec_admin",
        email="sec_adm@bankflow.synthetic",
        password_hash=hash_password("Admin@2026!"),
        role=UserRole.ADMINISTRATOR,
        is_active=True,
    )
    db_session.add(user_adm)
    db_session.flush()

    adm = Employee(
        user_id=user_adm.id,
        employee_code="ADM-SEC-001",
        full_name="Admin Eve",
        department="Executive IT",
        designation="System Administrator",
        branch_id="BR-MAIN-01",
    )
    db_session.add(adm)
    db_session.flush()

    tokens = {
        "cust_a": create_access_token(user_cust_a.id, user_cust_a.role.value, user_cust_a.username),
        "cust_b": create_access_token(user_cust_b.id, user_cust_b.role.value, user_cust_b.username),
        "employee": create_access_token(user_emp.id, user_emp.role.value, user_emp.username),
        "supervisor": create_access_token(user_sup.id, user_sup.role.value, user_sup.username),
        "admin": create_access_token(user_adm.id, user_adm.role.value, user_adm.username),
    }

    return {
        "user_cust_a": user_cust_a,
        "cust_a": cust_a,
        "acc_a": acc_a,
        "user_cust_b": user_cust_b,
        "cust_b": cust_b,
        "user_emp": user_emp,
        "emp": emp,
        "user_sup": user_sup,
        "sup": sup,
        "user_adm": user_adm,
        "adm": adm,
        "tokens": tokens,
    }


# ==============================================================================
# 1. Customer cannot access another customer's profile
# ==============================================================================
def test_customer_cannot_access_another_customer_profile(client: TestClient, security_users):
    """Ensures customer profile endpoint strictly scopes to authenticated identity."""
    token_a = security_users["tokens"]["cust_a"]
    resp = client.get("/api/customer/profile", headers={"Authorization": f"Bearer {token_a}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["customer_code"] == security_users["cust_a"].customer_code
    assert data["customer_code"] != security_users["cust_b"].customer_code
    assert data["full_name"] == "Alice Customer"


# ==============================================================================
# 2. Customer cannot access another customer's service request
# ==============================================================================
def test_customer_cannot_access_another_customer_service_request(client: TestClient, db_session: Session, security_users):
    """Verifies horizontal authorization boundary: Customer B cannot view Customer A's request."""
    cust_a = security_users["cust_a"]
    req = Request(
        request_id="BFA-REQ-ISOLATION-001",
        customer_id=cust_a.id,
        service_type=ServiceType.CHEQUE_BOOK,
        request_status=RequestStatus.NEW,
        priority="NORMAL",
        payload={"leaves_count": 25, "delivery_address": "123 Alice St"},
    )
    db_session.add(req)
    db_session.flush()

    token_b = security_users["tokens"]["cust_b"]
    # Customer B attempts to access Customer A's request
    resp = client.get(f"/api/customer/requests/{req.request_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert resp.status_code == 404
    assert "not authorized" in resp.json()["detail"].lower() or "not found" in resp.json()["detail"].lower()

    # Customer B attempts to submit correction for Customer A's request
    corr_resp = client.put(
        f"/api/customer/requests/{req.request_id}/correction",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"payload": {"leaves_count": 50}, "correction_notes": "Malicious edit"},
    )
    assert corr_resp.status_code == 404


# ==============================================================================
# 3. Employee cannot access administrator-only endpoints
# ==============================================================================
def test_employee_cannot_access_admin_endpoints(client: TestClient, security_users):
    """Verifies vertical authorization boundary: Bank Employee cannot access Admin APIs."""
    emp_token = security_users["tokens"]["employee"]
    headers = {"Authorization": f"Bearer {emp_token}"}

    # Attempt to list admin users
    resp_users = client.get("/api/bank/admin/users", headers=headers)
    assert resp_users.status_code == 403
    assert "administrator privileges required" in resp_users.json()["detail"].lower()

    # Attempt to modify a user role
    resp_role = client.put(
        f"/api/bank/admin/users/{security_users['user_emp'].id}/role",
        headers=headers,
        json={"role": "ADMINISTRATOR"},
    )
    assert resp_role.status_code == 403

    # Attempt to access security status
    resp_sec = client.get("/api/bank/admin/security-status", headers=headers)
    assert resp_sec.status_code == 403


# ==============================================================================
# 4. Supervisor can access permitted monitoring endpoints
# ==============================================================================
def test_supervisor_can_access_permitted_monitoring_endpoints(client: TestClient, security_users):
    """Verifies that a SUPERVISOR can access monitoring, simulation, and messaging endpoints."""
    sup_token = security_users["tokens"]["supervisor"]
    headers = {"Authorization": f"Bearer {sup_token}"}

    # Agent monitoring list
    resp_agents = client.get("/api/bank/agents", headers=headers)
    assert resp_agents.status_code == 200

    # Simulation telemetry
    resp_sim = client.get("/api/bank/simulation/status", headers=headers)
    assert resp_sim.status_code == 200

    # RabbitMQ messaging broker status
    resp_msg = client.get("/api/bank/messaging/status", headers=headers)
    assert resp_msg.status_code == 200

    # Agent communication throughput
    resp_comm = client.get("/api/bank/agents/communication", headers=headers)
    assert resp_comm.status_code == 200


# ==============================================================================
# 5. Invalid or expired JWT tokens are rejected
# ==============================================================================
def test_invalid_or_expired_jwt_tokens_rejected(client: TestClient, security_users):
    """Rejects missing, forged, revoked, or expired tokens with HTTP 401."""
    # 1. Missing token
    resp_missing = client.get("/api/customer/profile")
    assert resp_missing.status_code == 401

    # 2. Forged signature
    resp_forged = client.get("/api/customer/profile", headers={"Authorization": "Bearer forged.invalid.token"})
    assert resp_forged.status_code == 401

    # 3. Expired token
    expired_token = create_access_token(
        user_id=security_users["user_cust_a"].id,
        role="CUSTOMER",
        username="sec_cust_a",
        expires_delta=timedelta(seconds=-10),  # expired 10 seconds ago
    )
    resp_expired = client.get("/api/customer/profile", headers={"Authorization": f"Bearer {expired_token}"})
    assert resp_expired.status_code == 401

    # 4. Revoked token (after logout)
    valid_token = create_access_token(
        user_id=security_users["user_cust_a"].id,
        role="CUSTOMER",
        username="sec_cust_a",
    )
    revoke_token(valid_token)
    resp_revoked = client.get("/api/customer/profile", headers={"Authorization": f"Bearer {valid_token}"})
    assert resp_revoked.status_code == 401


# ==============================================================================
# 6. Incorrect passwords are rejected
# ==============================================================================
def test_incorrect_passwords_rejected(client: TestClient, security_users):
    """Rejects wrong passwords with clean safe error messages and records rate limits."""
    # Customer login with wrong password
    resp_cust = client.post(
        "/api/auth/customer/login",
        json={"username_or_email": "sec_cust_a", "password": "WrongPassword123!"},
    )
    assert resp_cust.status_code == 401
    assert "invalid username, email, or password" in resp_cust.json()["detail"].lower()

    # Bank employee login with wrong credentials
    resp_bank = client.post(
        "/api/auth/bank/login",
        json={"employee_id_or_username": "EMP-SEC-001", "password": "BadPassword999!"},
    )
    assert resp_bank.status_code == 401
    assert "invalid employee credentials" in resp_bank.json()["detail"].lower()


# ==============================================================================
# 7. Passwords are never stored in plain text and Argon2id enforced
# ==============================================================================
def test_passwords_never_stored_in_plaintext_and_argon2id_enforced(db_session: Session, client: TestClient, security_users):
    """Verifies that stored passwords use Argon2id and hashes never leak into API responses."""
    user = security_users["user_cust_a"]
    db_session.refresh(user)

    # Stored password check
    assert user.password_hash is not None
    assert user.password_hash != "Customer@2026!"
    assert user.password_hash.startswith("$argon2id$")
    assert verify_password("Customer@2026!", user.password_hash) is True

    # Ensure password_hash is not exposed in /api/auth/me
    token_a = security_users["tokens"]["cust_a"]
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_a}"})
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert "password" not in me_data
    assert "password_hash" not in me_data

    # Ensure password_hash is not exposed in /api/customer/profile
    prof_resp = client.get("/api/customer/profile", headers={"Authorization": f"Bearer {token_a}"})
    assert prof_resp.status_code == 200
    prof_data = prof_resp.json()
    assert "password" not in prof_data
    assert "password_hash" not in prof_data


# ==============================================================================
# 8. AES-256-GCM encryption and decryption work correctly
# ==============================================================================
def test_aes_256_gcm_encryption_and_decryption_accuracy():
    """Validates AES-256-GCM authenticated encryption round-trip and unique nonces."""
    secret_text = "Confidential Synthetic Account 987654321, Tax ID 123-45-6789"

    # Encrypt twice
    enc1 = encrypt_field(secret_text)
    enc2 = encrypt_field(secret_text)

    # Must start with version prefix
    assert enc1.startswith(ENCRYPTION_PREFIX)
    assert enc2.startswith(ENCRYPTION_PREFIX)

    # Must have distinct nonces / ciphertexts
    assert enc1 != enc2

    # Decrypt both back to identical plaintext
    assert decrypt_field(enc1) == secret_text
    assert decrypt_field(enc2) == secret_text

    # Test dictionary encryption
    sensitive_dict = {
        "account_id": 101,
        "delivery_address": "456 Private Ave, Suite 10",
        "tax_id": "999-88-7777",
        "public_note": "Handle promptly",
    }
    encrypted_dict = encrypt_payload_fields(sensitive_dict)
    assert encrypted_dict["account_id"] == 101
    assert encrypted_dict["public_note"] == "Handle promptly"
    assert encrypted_dict["delivery_address"].startswith(ENCRYPTION_PREFIX)
    assert encrypted_dict["tax_id"].startswith(ENCRYPTION_PREFIX)

    decrypted_dict = decrypt_payload_fields(encrypted_dict)
    assert decrypted_dict["delivery_address"] == "456 Private Ave, Suite 10"
    assert decrypted_dict["tax_id"] == "999-88-7777"


# ==============================================================================
# 9. Incorrect encryption keys or modified ciphertext cause safe failures
# ==============================================================================
def test_modified_ciphertext_and_wrong_key_cause_safe_failures():
    """Ensures AES-256-GCM authentication tags catch tampering and bad keys."""
    plaintext = "Sensitive Financial Information"
    enc = encrypt_field(plaintext)

    # 1. Tampering with ciphertext content
    tampered = enc[:-5] + "AAAAA"
    with pytest.raises(DecryptionError):
        decrypt_field(tampered)

    # 2. Decrypting with an incorrect 256-bit key
    wrong_key = b"\x00" * 32
    with pytest.raises(DecryptionError):
        decrypt_field(enc, key=wrong_key)

    # 3. Truncated invalid ciphertext
    with pytest.raises(DecryptionError):
        decrypt_field(f"{ENCRYPTION_PREFIX}SGVsbG8=")


# ==============================================================================
# 10. Unauthorized users cannot modify roles
# ==============================================================================
def test_unauthorized_users_cannot_modify_roles(client: TestClient, security_users):
    """Verifies that only ADMINISTRATOR can modify roles, and users cannot self-escalate."""
    cust_token = security_users["tokens"]["cust_a"]
    emp_token = security_users["tokens"]["employee"]
    adm_token = security_users["tokens"]["admin"]
    target_user_id = security_users["user_emp"].id

    # Customer cannot call admin endpoint
    resp_cust = client.put(
        f"/api/bank/admin/users/{target_user_id}/role",
        headers={"Authorization": f"Bearer {cust_token}"},
        json={"role": "ADMINISTRATOR"},
    )
    assert resp_cust.status_code == 403

    # Bank Employee cannot escalate roles
    resp_emp = client.put(
        f"/api/bank/admin/users/{target_user_id}/role",
        headers={"Authorization": f"Bearer {emp_token}"},
        json={"role": "ADMINISTRATOR"},
    )
    assert resp_emp.status_code == 403

    # Administrator can update role
    resp_adm = client.put(
        f"/api/bank/admin/users/{target_user_id}/role",
        headers={"Authorization": f"Bearer {adm_token}"},
        json={"role": "SUPERVISOR"},
    )
    assert resp_adm.status_code == 200
    assert resp_adm.json()["role"] == "SUPERVISOR"

    # Administrator cannot demote themselves
    admin_id = security_users["user_adm"].id
    resp_self_demote = client.put(
        f"/api/bank/admin/users/{admin_id}/role",
        headers={"Authorization": f"Bearer {adm_token}"},
        json={"role": "CUSTOMER"},
    )
    assert resp_self_demote.status_code == 400
    assert "cannot demote their own account" in resp_self_demote.json()["detail"].lower()


# ==============================================================================
# 11. Audit logs are created for important actions
# ==============================================================================
def test_audit_logs_created_for_important_actions(db_session: Session, security_users):
    """Verifies structured audit records are emitted with event_id, outcome, and timestamps."""
    user = security_users["user_cust_a"]
    entry = AuditService.record_event(
        db=db_session,
        action="SECURITY_CHECK",
        user_id=user.id,
        request_id="BFA-REQ-AUD-001",
        outcome="SUCCESS",
        description="Comprehensive security hardening check executed.",
        source_ip="192.168.1.100",
        entity_type="SYSTEM",
    )

    assert entry.id is not None
    assert entry.event_id is not None
    assert entry.event_id.startswith("AUD-")
    assert entry.action == "SECURITY_CHECK"
    assert entry.outcome == "SUCCESS"
    assert entry.request_id == "BFA-REQ-AUD-001"
    assert entry.source_ip == "192.168.1.100"


# ==============================================================================
# 12. Audit logs do not contain passwords or tokens
# ==============================================================================
def test_audit_logs_do_not_contain_passwords_or_tokens():
    """Ensures AuditService sanitizes leaked passwords, tokens, hashes, and secrets."""
    dirty_text = (
        "User tried logging in with password: SuperSecretPassword123! "
        "and bearer token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.dummy "
        "and encryption_key=0123456789abcdef "
        "and pin 4321."
    )
    clean_text = AuditService.sanitize_description(dirty_text)

    assert "SuperSecretPassword123!" not in clean_text
    assert "eyJhbGci" not in clean_text
    assert "0123456789abcdef" not in clean_text
    assert "4321" not in clean_text
    assert "[REDACTED_BY_SECURITY_POLICY]" in clean_text


# ==============================================================================
# 13. Malformed RabbitMQ messages are rejected safely
# ==============================================================================
def test_malformed_rabbitmq_messages_rejected_safely():
    """Ensures Pydantic schema rejects malformed messages or forbidden credentials."""
    # 1. Missing required field
    with pytest.raises(Exception):
        StandardBankingMessage(
            request_id="BFA-REQ-TEST-001",
            # missing sender_agent_id, receiver_agent_id, event_type
        )

    # 2. Forbidden credential in payload (password, pin, jwt_token)
    with pytest.raises(ValueError) as exc_info:
        StandardBankingMessage(
            request_id="BFA-REQ-BAD-001",
            request_version=0,
            sender_agent_id="AGT-TEST",
            receiver_agent_id="AGT-INTAKE",
            event_type=BankingEventType.REQUEST_CREATED,
            payload={"password": "PlainPasswordLeaked!"},
        )
    assert "forbidden" in str(exc_info.value).lower()


# ==============================================================================
# 14. Request size limits and defensive security headers
# ==============================================================================
def test_request_size_limit_and_security_headers(client: TestClient):
    """Verifies HTTP 413 on payload too large and presence of defensive security headers."""
    # Test defensive headers on a standard request
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert resp.headers.get("X-XSS-Protection") == "1; mode=block"
    assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    # Test payload size limit (> 2 MB)
    huge_data = {"text": "A" * (2 * 1024 * 1024 + 100)}
    resp_large = client.post("/api/auth/customer/login", json=huge_data)
    assert resp_large.status_code == 413
