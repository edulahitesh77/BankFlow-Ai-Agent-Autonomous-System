"""
BankFlow AI - Database Engine and Session Management
Configures SQLAlchemy connection pooling, declarative base, and session dependency.
"""

import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.config import settings

logger = logging.getLogger(__name__)

# Primary database engine
# pool_pre_ping tests connections before giving them to sessions, preventing stale connection errors
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.DEBUG,
)

# Thread-local session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Declarative base model class
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding an isolated database session.
    Closes the session cleanly upon request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connectivity() -> dict:
    """
    Safely ping the database and verify connectivity.
    Does not expose passwords or sensitive configuration in responses or logs.
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            scalar = result.scalar()
            if scalar == 1:
                return {
                    "status": "connected",
                    "reachable": True,
                    "database": settings.DB_NAME,
                    "host": settings.DB_HOST,
                    "port": settings.DB_PORT,
                }
            return {
                "status": "error",
                "reachable": False,
                "error": "Unexpected ping result from database",
            }
    except Exception as exc:
        logger.error("Database connectivity check failed: %s", str(exc))
        return {
            "status": "disconnected",
            "reachable": False,
            "error": "Unable to establish connection to database server",
        }


class BranchDatabaseManager:
    """
    Manages isolated connection pools and sessions for individual bank branches:
    - Bengaluru (BLR001)
    - Chennai (CHE001)
    - Hyderabad (HYD001)

    Enforces branch database separation: each branch accesses its own dedicated database.
    Direct cross-branch queries are prohibited; information exchange occurs strictly
    via the Federation Gateway.
    """

    _engines: dict = {}
    _sessionmakers: dict = {}

    @classmethod
    def get_engine(cls, branch_id: str, is_test: bool = False):
        """Returns or creates the engine for a specific branch."""
        key = f"{branch_id.upper()}_{'TEST' if is_test else 'PROD'}"
        if key not in cls._engines:
            url = settings.get_branch_database_url(branch_id, is_test=is_test)
            cls._engines[key] = create_engine(
                url,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
                echo=settings.DEBUG,
            )
        return cls._engines[key]

    @classmethod
    def get_sessionmaker(cls, branch_id: str, is_test: bool = False) -> sessionmaker:
        """Returns or creates the sessionmaker for a specific branch."""
        key = f"{branch_id.upper()}_{'TEST' if is_test else 'PROD'}"
        if key not in cls._sessionmakers:
            b_engine = cls.get_engine(branch_id, is_test=is_test)
            cls._sessionmakers[key] = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=b_engine,
            )
        return cls._sessionmakers[key]

    @classmethod
    def get_session(cls, branch_id: str, is_test: bool = False) -> Session:
        """Instantiates an isolated session for a specific branch."""
        factory = cls.get_sessionmaker(branch_id, is_test=is_test)
        return factory()

    @classmethod
    def check_all_branches(cls) -> dict:
        """Verifies database connectivity across all federated branches."""
        results = {}
        for b_id in ["BLR001", "CHE001", "HYD001"]:
            try:
                b_engine = cls.get_engine(b_id)
                with b_engine.connect() as conn:
                    scalar = conn.execute(text("SELECT 1")).scalar()
                    results[b_id] = {
                        "reachable": scalar == 1,
                        "status": "connected" if scalar == 1 else "error",
                    }
            except Exception as e:
                results[b_id] = {
                    "reachable": False,
                    "status": "disconnected",
                    "error": str(e),
                }
        return results


def get_branch_db(branch_id: str = "BLR001") -> Generator[Session, None, None]:
    """FastAPI dependency yielding an isolated session for a specified branch."""
    db = BranchDatabaseManager.get_session(branch_id)
    try:
        yield db
    finally:
        db.close()

