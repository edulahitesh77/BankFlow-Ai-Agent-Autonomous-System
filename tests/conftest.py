"""
BankFlow AI - Shared Pytest Fixtures
Provides reusable test database sessions, synthetic customer and account fixtures.
"""

import sys
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Ensure backend directory is in sys.path
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.config import settings
from app.database import Base
from app.models.user import User, UserRole
from app.models.customer import Customer
from app.models.account import Account
from app.auth.security import hash_password

test_engine = create_engine(settings.test_database_url, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def init_test_database():
    """Ensure all database tables exist in the test database."""
    Base.metadata.create_all(bind=test_engine)
    yield


@pytest.fixture(scope="function")
def db_session() -> Session:
    """Provides a transactional database session rolled back after test execution."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def sample_customer_and_account(db_session: Session):
    """Creates a sample test user, customer, and synthetic account."""
    user = User(
        username="agent_test_user",
        email="agent_test@bankflow.synthetic",
        password_hash=hash_password("Password@2026!"),
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    customer = Customer(
        user_id=user.id,
        customer_code="CUST-AGENT-TEST-01",
        full_name="Agent Test Customer",
        email=user.email,
        phone="+1-555-0199",
        branch_id="BR-MAIN-01",
    )
    db_session.add(customer)
    db_session.flush()

    account = Account(
        customer_id=customer.id,
        synthetic_account_number="ACC-TEST-99001",
        account_type="SAVINGS",
        account_status="ACTIVE",
        branch_id="BR-MAIN-01",
    )
    db_session.add(account)
    db_session.flush()

    return customer, account
