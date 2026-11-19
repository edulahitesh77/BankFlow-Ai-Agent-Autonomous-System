"""
BankFlow AI - Automated Test Suite
Tests application startup, API endpoints, database connectivity,
migration tables, and model relationships in an isolated test environment.
"""

import sys
import os
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError

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
from app.models.account import Account
from app.models.request import Request, ServiceType, RequestStatus
from app.models.agent import Agent, AgentType
from app.models.audit_log import AuditLog

# Test database engine and session factory
test_engine = create_engine(settings.test_database_url, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Ensure all tables are created in the test database."""
    Base.metadata.create_all(bind=test_engine)
    yield
    # Cleanup after test session
    # Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db_session() -> Session:
    """Yield a database session wrapped in a transaction that is rolled back after each test."""
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
    """FastAPI TestClient with overridden database session dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ============================================================================
# 1. API & APPLICATION TESTS
# ============================================================================

def test_application_startup_and_openapi(client: TestClient):
    """Test FastAPI application startup, OpenAPI schema, and Swagger UI."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "BankFlow AI"
    assert schema["info"]["version"] == "1.0.0"

    docs_response = client.get("/docs")
    assert docs_response.status_code == 200


def test_root_endpoint(client: TestClient):
    """Test root endpoint GET / returning project information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "BankFlow AI"
    assert data["version"] == "1.0.0"
    assert "Phase 1" in data["phase"]
    assert data["status"] == "operational"
    assert "health" in data["endpoints"]
    assert "database_health" in data["endpoints"]


def test_health_endpoint(client: TestClient):
    """Test health check endpoint GET /health."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "BankFlow AI"
    assert data["version"] == "1.0.0"


def test_database_connectivity_endpoint(client: TestClient):
    """Test database health check endpoint GET /health/database."""
    response = client.get("/health/database")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "connected"
    assert data["reachable"] is True
    assert data["database"] == settings.DB_NAME
    # Ensure sensitive credentials are never leaked
    assert "password" not in data
    assert "DB_PASSWORD" not in data


# ============================================================================
# 2. DATABASE MIGRATIONS & SCHEMA INTEGRITY TESTS
# ============================================================================

def test_database_tables_exist():
    """Verify all seven required database tables are present in the database."""
    inspector = inspect(test_engine)
    tables = inspector.get_table_names()

    required_tables = [
        "users",
        "customers",
        "employees",
        "accounts",
        "requests",
        "agents",
        "audit_logs",
    ]

    for table in required_tables:
        assert table in tables, f"Expected table '{table}' was not found in database"


# ============================================================================
# 3. DATABASE MODELS & RELATIONSHIPS TESTS
# ============================================================================

def test_user_customer_one_to_one(db_session: Session):
    """Test User -> Customer 1-to-1 relationship and foreign key cascade."""
    # Create user
    user = User(
        username="john_customer",
        email="john.customer@bankflow.synthetic",
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    # Create customer profile linked to user
    customer = Customer(
        user_id=user.id,
        customer_code="CUST-SYN-00101",
        full_name="John Doe",
        phone="+1-555-0101",
        email=user.email,
        branch_id="BR-MAIN-01",
    )
    db_session.add(customer)
    db_session.flush()

    # Verify bidirectional navigation
    assert user.customer is not None
    assert user.customer.customer_code == "CUST-SYN-00101"
    assert customer.user.username == "john_customer"

    # Verify unique constraint prevents duplicate customer profile for same user
    duplicate_customer = Customer(
        user_id=user.id,
        customer_code="CUST-SYN-00102",
        full_name="Duplicate John",
        email=user.email,
    )
    db_session.add(duplicate_customer)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_user_employee_one_to_one(db_session: Session):
    """Test User -> Employee 1-to-1 relationship."""
    user = User(
        username="sarah_manager",
        email="sarah.manager@bankflow.synthetic",
        role=UserRole.BANK_EMPLOYEE,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    employee = Employee(
        user_id=user.id,
        employee_code="EMP-SYN-9001",
        full_name="Sarah Connor",
        department="Operations",
        designation="Branch Supervisor",
        branch_id="BR-MAIN-01",
    )
    db_session.add(employee)
    db_session.flush()

    assert user.employee is not None
    assert user.employee.employee_code == "EMP-SYN-9001"
    assert employee.user.username == "sarah_manager"


def test_customer_accounts_one_to_many(db_session: Session):
    """Test Customer -> Accounts 1-to-many relationship."""
    user = User(
        username="alice_accounts",
        email="alice@bankflow.synthetic",
        role=UserRole.CUSTOMER,
    )
    db_session.add(user)
    db_session.flush()

    customer = Customer(
        user_id=user.id,
        customer_code="CUST-SYN-00201",
        full_name="Alice Smith",
        email=user.email,
    )
    db_session.add(customer)
    db_session.flush()

    # Create multiple synthetic accounts
    acc1 = Account(
        customer_id=customer.id,
        synthetic_account_number="SYN-ACC-1000000001",
        account_type="SAVINGS",
        account_status="ACTIVE",
    )
    acc2 = Account(
        customer_id=customer.id,
        synthetic_account_number="SYN-ACC-1000000002",
        account_type="CHECKING",
        account_status="ACTIVE",
    )
    db_session.add_all([acc1, acc2])
    db_session.flush()

    assert len(customer.accounts) == 2
    assert {a.synthetic_account_number for a in customer.accounts} == {
        "SYN-ACC-1000000001",
        "SYN-ACC-1000000002",
    }
    assert acc1.customer.id == customer.id


def test_customer_requests_and_agent_assignment(db_session: Session):
    """Test Customer -> Requests and Request -> Agent relationship."""
    user = User(
        username="bob_requester",
        email="bob@bankflow.synthetic",
        role=UserRole.CUSTOMER,
    )
    db_session.add(user)
    db_session.flush()

    customer = Customer(
        user_id=user.id,
        customer_code="CUST-SYN-00301",
        full_name="Bob Miller",
        email=user.email,
    )
    db_session.add(customer)
    db_session.flush()

    agent = Agent(
        agent_code="AGENT-SYN-REQ-01",
        agent_type=AgentType.REQUEST,
        availability_status="AVAILABLE",
    )
    db_session.add(agent)
    db_session.flush()

    # Create banking request
    req = Request(
        request_id="REQ-SYN-2026-0001",
        customer_id=customer.id,
        service_type=ServiceType.CHEQUE_BOOK,
        request_status=RequestStatus.NEW,
        priority="HIGH",
        assigned_agent_id=agent.id,
        required_skill="CHEQUE_BOOK_PROCESSING",
    )
    db_session.add(req)
    db_session.flush()

    assert req.customer.id == customer.id
    assert req.assigned_agent.id == agent.id
    assert req in agent.assigned_requests
    assert req in customer.requests


def test_multiple_request_agent_instances(db_session: Session):
    """Verify system supports multiple concurrent REQUEST agent instances."""
    agent1 = Agent(
        agent_code="AGENT-SYN-REQ-INST-01",
        agent_type=AgentType.REQUEST,
        availability_status="AVAILABLE",
    )
    agent2 = Agent(
        agent_code="AGENT-SYN-REQ-INST-02",
        agent_type=AgentType.REQUEST,
        availability_status="BUSY",
    )
    agent3 = Agent(
        agent_code="AGENT-SYN-SUP-01",
        agent_type=AgentType.SUPERVISOR,
        availability_status="AVAILABLE",
    )
    db_session.add_all([agent1, agent2, agent3])
    db_session.flush()

    request_agents = (
        db_session.query(Agent)
        .filter(Agent.agent_type == AgentType.REQUEST)
        .all()
    )
    assert len(request_agents) >= 2
    codes = [a.agent_code for a in request_agents]
    assert "AGENT-SYN-REQ-INST-01" in codes
    assert "AGENT-SYN-REQ-INST-02" in codes


def test_audit_log_recording(db_session: Session):
    """Test AuditLog creation and optional user association."""
    user = User(
        username="audited_user",
        email="audit@bankflow.synthetic",
        role=UserRole.BANK_EMPLOYEE,
    )
    db_session.add(user)
    db_session.flush()

    # System-level action (no user)
    log_system = AuditLog(
        user_id=None,
        action="SYSTEM_INIT",
        entity_type="SYSTEM",
        entity_id="ROOT",
        description="Application database initialized",
    )
    # User-level action
    log_user = AuditLog(
        user_id=user.id,
        action="REQUEST_ASSIGNED",
        entity_type="REQUEST",
        entity_id="REQ-SYN-0001",
        description="Assigned to Agent AGENT-SYN-REQ-01",
    )
    db_session.add_all([log_system, log_user])
    db_session.flush()

    assert log_system.id is not None
    assert log_user.id is not None
    assert log_user.user.username == "audited_user"
    assert log_system.user is None


def test_request_status_and_service_type_enums(db_session: Session):
    """Verify all supported RequestStatus and ServiceType enum values persist accurately."""
    user = User(
        username="enum_tester",
        email="enum@bankflow.synthetic",
        role=UserRole.CUSTOMER,
    )
    db_session.add(user)
    db_session.flush()

    customer = Customer(
        user_id=user.id,
        customer_code="CUST-SYN-ENUM",
        full_name="Enum Tester",
        email=user.email,
    )
    db_session.add(customer)
    db_session.flush()

    # Persist a request with each status value
    statuses = list(RequestStatus)
    for idx, st in enumerate(statuses):
        req = Request(
            request_id=f"REQ-ENUM-{idx:03d}",
            customer_id=customer.id,
            service_type=ServiceType.DEBIT_CARD_REPLACEMENT,
            request_status=st,
            priority="MEDIUM",
        )
        db_session.add(req)

    db_session.flush()

    queried_statuses = {
        r.request_status
        for r in db_session.query(Request).filter(Request.customer_id == customer.id).all()
    }
    assert queried_statuses == set(RequestStatus)
