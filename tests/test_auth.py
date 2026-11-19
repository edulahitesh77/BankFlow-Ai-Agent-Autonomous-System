"""
BankFlow AI - Phase 2 Authentication & Security Test Suite
Tests customer registration, dual login systems, RBAC permissions,
Argon2id hashing, rate limiting, and token validation.
"""

import sys
import os
import pytest
from datetime import timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Ensure backend directory is in sys.path
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.main import app
from app.config import settings
from app.database import Base, get_db
from app.models.user import User, UserRole
from app.models.customer import Customer
from app.models.employee import Employee
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
from app.services.user_service import UserService

# Test database setup
test_engine = create_engine(settings.test_database_url, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield


@pytest.fixture(scope="function")
def db_session() -> Session:
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> TestClient:
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    # Clear rate limiter and revoked tokens before each test
    login_rate_limiter.reset_all()
    clear_revoked_tokens()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ============================================================================
# 1. ARGON2ID & SECURITY UNIT TESTS
# ============================================================================

def test_argon2id_hashing_and_verification():
    """Verify that password hashing uses Argon2id format and verifies correctly."""
    raw_pw = "BankSecure@2026!"
    hashed = hash_password(raw_pw)

    # Must be valid Argon2id hash format
    assert hashed.startswith("$argon2id$")
    assert verify_password(raw_pw, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False
    assert verify_password("", hashed) is False


def test_password_strength_validation():
    """Test banking password complexity policy."""
    # Too short
    ok, msg = validate_password_strength("Ab1!")
    assert not ok and "at least 8" in msg

    # Missing uppercase
    ok, msg = validate_password_strength("lowercase123!")
    assert not ok and "uppercase" in msg

    # Missing lowercase
    ok, msg = validate_password_strength("UPPERCASE123!")
    assert not ok and "lowercase" in msg

    # Missing number
    ok, msg = validate_password_strength("LettersOnly!@#")
    assert not ok and "numeric" in msg

    # Missing symbol
    ok, msg = validate_password_strength("Letters123456")
    assert not ok and "special" in msg

    # Valid
    ok, _ = validate_password_strength("SecureBank@2026")
    assert ok is True


# ============================================================================
# 2. CUSTOMER AUTHENTICATION TESTS
# ============================================================================

def test_customer_registration_success(client: TestClient, db_session: Session):
    """Test successful customer registration with database verification."""
    payload = {
        "full_name": "Eleanor Rigby",
        "email": "eleanor.rigby@bankflow.synthetic",
        "phone": "+1-555-0199",
        "username": "eleanor_customer",
        "password": "SecurePassword@123",
        "confirm_password": "SecurePassword@123",
    }

    response = client.post("/api/auth/customer/register", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert "access_token" in data
    assert data["role"] == "CUSTOMER"
    assert data["redirect_url"] == "/customer/dashboard"
    assert data["username"] == "eleanor_customer"

    # Verify user record in database
    user = db_session.query(User).filter(User.username == "eleanor_customer").first()
    assert user is not None
    assert user.role == UserRole.CUSTOMER
    assert user.is_active is True
    assert user.password_hash.startswith("$argon2id$")

    # Verify customer record linked
    assert user.customer is not None
    assert user.customer.full_name == "Eleanor Rigby"
    assert user.customer.customer_code.startswith("CUST-SYN-")

    # Verify audit log recorded
    audit = db_session.query(AuditLog).filter(AuditLog.user_id == user.id).first()
    assert audit is not None
    assert audit.action == "CUSTOMER_REGISTRATION"


def test_customer_registration_duplicate_email(client: TestClient):
    """Test rejection of duplicate email during customer registration."""
    payload = {
        "full_name": "User One",
        "email": "duplicate@bankflow.synthetic",
        "username": "user_one_orig",
        "password": "Password@123",
        "confirm_password": "Password@123",
    }
    res1 = client.post("/api/auth/customer/register", json=payload)
    assert res1.status_code == 201

    payload2 = {
        "full_name": "User Two",
        "email": "duplicate@bankflow.synthetic",
        "username": "user_two_diff",
        "password": "Password@123",
        "confirm_password": "Password@123",
    }
    res2 = client.post("/api/auth/customer/register", json=payload2)
    assert res2.status_code == 400
    assert "Email address is already registered" in res2.json()["detail"]


def test_customer_registration_duplicate_username(client: TestClient):
    """Test rejection of duplicate username during customer registration."""
    payload = {
        "full_name": "User Alpha",
        "email": "alpha@bankflow.synthetic",
        "username": "same_username",
        "password": "Password@123",
        "confirm_password": "Password@123",
    }
    res1 = client.post("/api/auth/customer/register", json=payload)
    assert res1.status_code == 201

    payload2 = {
        "full_name": "User Beta",
        "email": "beta@bankflow.synthetic",
        "username": "same_username",
        "password": "Password@123",
        "confirm_password": "Password@123",
    }
    res2 = client.post("/api/auth/customer/register", json=payload2)
    assert res2.status_code == 400
    assert "Username is already registered" in res2.json()["detail"]


def test_customer_registration_password_mismatch(client: TestClient):
    """Test validation rejection when password and confirm_password do not match."""
    payload = {
        "full_name": "Mismatch Tester",
        "email": "mismatch@bankflow.synthetic",
        "username": "mismatch_user",
        "password": "Password@123",
        "confirm_password": "DifferentPassword@123",
    }
    res = client.post("/api/auth/customer/register", json=payload)
    assert res.status_code == 422  # Pydantic validation error


def test_customer_login_success_by_username_and_email(client: TestClient):
    """Test customer authentication with both username and registered email."""
    # Register customer
    reg_payload = {
        "full_name": "Clara Oswald",
        "email": "clara.oswald@bankflow.synthetic",
        "username": "clara_oswald",
        "password": "SecurePassword@2026",
        "confirm_password": "SecurePassword@2026",
    }
    client.post("/api/auth/customer/register", json=reg_payload)

    # 1. Login with username
    login_user = client.post(
        "/api/auth/customer/login",
        json={"username_or_email": "clara_oswald", "password": "SecurePassword@2026"},
    )
    assert login_user.status_code == 200
    assert login_user.json()["redirect_url"] == "/customer/dashboard"
    assert login_user.json()["role"] == "CUSTOMER"

    # 2. Login with email
    login_email = client.post(
        "/api/auth/customer/login",
        json={"username_or_email": "clara.oswald@bankflow.synthetic", "password": "SecurePassword@2026"},
    )
    assert login_email.status_code == 200
    assert login_email.json()["role"] == "CUSTOMER"


def test_customer_login_invalid_password(client: TestClient):
    """Test customer login rejection on invalid password."""
    reg_payload = {
        "full_name": "David Tennant",
        "email": "david@bankflow.synthetic",
        "username": "david_tennant",
        "password": "CorrectPassword@123",
        "confirm_password": "CorrectPassword@123",
    }
    client.post("/api/auth/customer/register", json=reg_payload)

    response = client.post(
        "/api/auth/customer/login",
        json={"username_or_email": "david_tennant", "password": "IncorrectPassword@999"},
    )
    assert response.status_code == 401
    assert "Invalid username, email, or password" in response.json()["detail"]


def test_customer_profile_access(client: TestClient):
    """Test customer accessing their own profile."""
    reg_payload = {
        "full_name": "Rose Tyler",
        "email": "rose@bankflow.synthetic",
        "username": "rose_tyler",
        "password": "RosePassword@2026",
        "confirm_password": "RosePassword@2026",
    }
    reg_res = client.post("/api/auth/customer/register", json=reg_payload)
    token = reg_res.json()["access_token"]

    response = client.get(
        "/api/customer/profile",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    profile = response.json()
    assert profile["full_name"] == "Rose Tyler"
    assert profile["email"] == "rose@bankflow.synthetic"
    assert profile["role"] == "CUSTOMER"
    assert profile["customer_code"].startswith("CUST-SYN-")


def test_customer_cannot_access_bank_routes(client: TestClient):
    """Verify that an authenticated CUSTOMER cannot access BANK_EMPLOYEE endpoints."""
    reg_payload = {
        "full_name": "Intruder Customer",
        "email": "intruder@bankflow.synthetic",
        "username": "intruder_cust",
        "password": "Password@123",
        "confirm_password": "Password@123",
    }
    reg_res = client.post("/api/auth/customer/register", json=reg_payload)
    customer_token = reg_res.json()["access_token"]

    # Customer attempts to access bank employee profile
    response = client.get(
        "/api/bank/profile",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert response.status_code == 403
    assert "Bank employee privileges required" in response.json()["detail"]


# ============================================================================
# 3. BANK EMPLOYEE AUTHENTICATION TESTS
# ============================================================================

def test_bank_employee_login_success(client: TestClient, db_session: Session):
    """Test successful bank employee authentication via employee code and username."""
    # Provision employee
    user, employee = UserService.provision_bank_employee(
        db=db_session,
        username="officer_smith",
        email="officer.smith@bankflow.synthetic",
        password="BankOfficer@2026!",
        employee_code="EMP-SYN-8888",
        full_name="Agent Smith",
        department="Audit & Oversight",
        designation="Principal Auditor",
        branch_id="BR-MAIN-001",
    )

    # 1. Login with employee code
    res_code = client.post(
        "/api/auth/bank/login",
        json={"employee_id_or_username": "EMP-SYN-8888", "password": "BankOfficer@2026!"},
    )
    assert res_code.status_code == 200
    data_code = res_code.json()
    assert data_code["role"] == "BANK_EMPLOYEE"
    assert data_code["redirect_url"] == "/bank/dashboard"
    assert "access_token" in data_code

    # 2. Login with username
    res_user = client.post(
        "/api/auth/bank/login",
        json={"employee_id_or_username": "officer_smith", "password": "BankOfficer@2026!"},
    )
    assert res_user.status_code == 200
    assert res_user.json()["role"] == "BANK_EMPLOYEE"


def test_bank_employee_login_invalid_credentials(client: TestClient, db_session: Session):
    """Test bank employee login failure with wrong password or non-existent code."""
    UserService.provision_bank_employee(
        db=db_session,
        username="teller_jane",
        email="teller.jane@bankflow.synthetic",
        password="CorrectPassword@123!",
        employee_code="EMP-SYN-7777",
        full_name="Jane Doe",
    )

    # Wrong password
    res1 = client.post(
        "/api/auth/bank/login",
        json={"employee_id_or_username": "EMP-SYN-7777", "password": "WrongPassword@999"},
    )
    assert res1.status_code == 401
    assert "Invalid employee credentials" in res1.json()["detail"]

    # Non-existent employee
    res2 = client.post(
        "/api/auth/bank/login",
        json={"employee_id_or_username": "EMP-SYN-0000", "password": "AnyPassword@123!"},
    )
    assert res2.status_code == 401


def test_bank_employee_profile_access(client: TestClient, db_session: Session):
    """Test employee accessing internal employee profile."""
    user, employee = UserService.provision_bank_employee(
        db=db_session,
        username="supervisor_dan",
        email="dan@bankflow.synthetic",
        password="SupervisorPassword@2026!",
        employee_code="EMP-SYN-5555",
        full_name="Daniel Jackson",
        department="Operations",
        designation="Senior Supervisor",
    )

    login_res = client.post(
        "/api/auth/bank/login",
        json={"employee_id_or_username": "EMP-SYN-5555", "password": "SupervisorPassword@2026!"},
    )
    token = login_res.json()["access_token"]

    response = client.get(
        "/api/bank/profile",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["employee_code"] == "EMP-SYN-5555"
    assert data["full_name"] == "Daniel Jackson"
    assert data["department"] == "Operations"
    assert data["role"] == "BANK_EMPLOYEE"


def test_bank_employee_cannot_access_customer_profile(client: TestClient, db_session: Session):
    """Verify that a BANK_EMPLOYEE cannot access customer-specific endpoints."""
    UserService.provision_bank_employee(
        db=db_session,
        username="clerk_bob",
        email="bob.clerk@bankflow.synthetic",
        password="ClerkPassword@2026!",
        employee_code="EMP-SYN-4444",
        full_name="Bob Clerk",
    )

    login_res = client.post(
        "/api/auth/bank/login",
        json={"employee_id_or_username": "clerk_bob", "password": "ClerkPassword@2026!"},
    )
    token = login_res.json()["access_token"]

    # Employee attempts to access customer profile endpoint
    response = client.get(
        "/api/customer/profile",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    assert "Customer privileges required" in response.json()["detail"]


# ============================================================================
# 4. TOKEN & SECURITY INTEGRITY TESTS
# ============================================================================

def test_missing_token_rejection(client: TestClient):
    """Verify unauthenticated requests return HTTP 401."""
    res1 = client.get("/api/customer/profile")
    assert res1.status_code == 401
    assert "missing" in res1.json()["detail"].lower()

    res2 = client.get("/api/bank/profile")
    assert res2.status_code == 401


def test_invalid_jwt_token_rejection(client: TestClient):
    """Verify malformed or forged JWT tokens return HTTP 401."""
    response = client.get(
        "/api/customer/profile",
        headers={"Authorization": "Bearer not.a.valid.jwt.token"},
    )
    assert response.status_code == 401


def test_expired_jwt_rejection(client: TestClient, db_session: Session):
    """Verify expired tokens are rejected with HTTP 401."""
    user = User(
        username="expired_user",
        email="expired@bankflow.synthetic",
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    # Create token expired in the past
    expired_token = create_access_token(
        user_id=user.id,
        role=user.role.value,
        username=user.username,
        expires_delta=timedelta(seconds=-10),
    )

    response = client.get(
        "/api/customer/profile",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()


def test_inactive_account_rejection(client: TestClient, db_session: Session):
    """Verify that deactivated or inactive accounts cannot access protected endpoints."""
    user = User(
        username="inactive_user",
        email="inactive@bankflow.synthetic",
        role=UserRole.CUSTOMER,
        is_active=False,  # Deactivated
    )
    db_session.add(user)
    db_session.flush()

    token = create_access_token(
        user_id=user.id,
        role=user.role.value,
        username=user.username,
    )

    response = client.get(
        "/api/customer/profile",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert "inactive" in response.json()["detail"].lower()


def test_token_revocation_on_logout(client: TestClient):
    """Verify that logging out revokes the JWT and subsequent requests are rejected."""
    # Register customer
    reg_payload = {
        "full_name": "Logout Tester",
        "email": "logout@bankflow.synthetic",
        "username": "logout_tester",
        "password": "Password@123!",
        "confirm_password": "Password@123!",
    }
    reg_res = client.post("/api/auth/customer/register", json=reg_payload)
    token = reg_res.json()["access_token"]

    # Verify profile works before logout
    res1 = client.get(
        "/api/customer/profile",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res1.status_code == 200

    # Call logout
    logout_res = client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert logout_res.status_code == 200

    # Verify token is now revoked and rejected
    res2 = client.get(
        "/api/customer/profile",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res2.status_code == 401
    assert "revoked" in res2.json()["detail"].lower()


def test_login_rate_limiting(client: TestClient):
    """Verify that repeated failed login attempts trigger HTTP 429 Too Many Requests."""
    username = "ratelimit_target"
    max_attempts = settings.RATE_LIMIT_LOGIN_MAX_ATTEMPTS

    # Fail login up to max_attempts
    for _ in range(max_attempts):
        res = client.post(
            "/api/auth/customer/login",
            json={"username_or_email": username, "password": "WrongPassword@999"},
        )
        assert res.status_code == 401

    # The next attempt must be rate-limited with HTTP 429
    blocked_res = client.post(
        "/api/auth/customer/login",
        json={"username_or_email": username, "password": "WrongPassword@999"},
    )
    assert blocked_res.status_code == 429
    assert "Too many failed login attempts" in blocked_res.json()["detail"]
    assert "Retry-After" in blocked_res.headers
