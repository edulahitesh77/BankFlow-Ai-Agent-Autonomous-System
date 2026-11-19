"""
BankFlow AI - Application Configuration
Loads configuration from environment variables and .env file.
Credentials and secrets are kept secure and never exposed.
"""

from functools import lru_cache
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application metadata
    APP_NAME: str = "BankFlow AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Database parameters
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_NAME: str = "bankflow_ai"
    TEST_DB_NAME: str = "bankflow_ai_test"

    # Multi-Branch Database parameters (Phase 10)
    BLR_DB_NAME: str = "bankflow_ai_blr"
    CHE_DB_NAME: str = "bankflow_ai_che"
    HYD_DB_NAME: str = "bankflow_ai_hyd"
    BLR_TEST_DB_NAME: str = "bankflow_ai_test_blr"
    CHE_TEST_DB_NAME: str = "bankflow_ai_test_che"
    HYD_TEST_DB_NAME: str = "bankflow_ai_test_hyd"

    # Direct database URL overrides (optional)
    DATABASE_URL: Union[str, None] = None
    TEST_DATABASE_URL: Union[str, None] = None
    BLR_DATABASE_URL: Union[str, None] = None
    CHE_DATABASE_URL: Union[str, None] = None
    HYD_DATABASE_URL: Union[str, None] = None

    # Multi-Branch Federation Security (Phase 10)
    FEDERATION_ENABLED: bool = True
    FEDERATION_GATEWAY_SECRET: str = "bankflow-fed-gateway-root-secret-2026-key"
    BLR_BRANCH_SECRET: str = "blr_fed_key_2026_secret"
    CHE_BRANCH_SECRET: str = "che_fed_key_2026_secret"
    HYD_BRANCH_SECRET: str = "hyd_fed_key_2026_secret"

    # Sensitive Data Encryption Configuration (AES-256-GCM)
    # Must be 32 bytes (64 hex characters) or a secure passphrase
    DATA_ENCRYPTION_KEY: str = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"

    # API Security & Request Body Limits
    MAX_REQUEST_BODY_SIZE_BYTES: int = 2 * 1024 * 1024  # 2 MB limit
    ENABLE_SECURITY_HEADERS: bool = True

    # JWT Authentication Configuration
    JWT_SECRET_KEY: str = "bankflow-secure-jwt-secret-key-development-environment-2026-simulation-change-in-prod"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REMEMBER_ME_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Rate Limiting Configuration
    RATE_LIMIT_LOGIN_MAX_ATTEMPTS: int = 5
    RATE_LIMIT_LOGIN_WINDOW_SECONDS: int = 300  # 5 minutes lockout

    # Seed Employee Credentials (for development provisioning)
    SEED_EMPLOYEE_USERNAME: str = "bank_admin"
    SEED_EMPLOYEE_EMAIL: str = "employee@bankflow.synthetic"
    SEED_EMPLOYEE_PASSWORD: str = "Employee@2026!"
    SEED_EMPLOYEE_CODE: str = "EMP-SYN-0001"
    SEED_EMPLOYEE_NAME: str = "Alexander Vance"
    SEED_EMPLOYEE_DEPARTMENT: str = "Central Operations"
    SEED_EMPLOYEE_DESIGNATION: str = "Senior Bank Officer"
    SEED_EMPLOYEE_BRANCH: str = "BR-MAIN-001"

    # CORS settings
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # RabbitMQ Message Broker Configuration
    RABBITMQ_HOST: str = "127.0.0.1"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_VHOST: str = "/"
    RABBITMQ_URL: Union[str, None] = None
    RABBITMQ_EXCHANGE: str = "bankflow.events"
    RABBITMQ_DLX_EXCHANGE: str = "bankflow.dlx"
    RABBITMQ_PREFETCH_COUNT: int = 10
    RABBITMQ_MAX_RETRIES: int = 3
    RABBITMQ_RETRY_DELAY_SECONDS: float = 1.0

    # Phase 8: Agent Health, Heartbeat & Timeout Configuration
    AGENT_HEARTBEAT_INTERVAL_SECONDS: float = 5.0
    AGENT_HEARTBEAT_TIMEOUT_SECONDS: float = 15.0
    AGENT_PROCESSING_TIMEOUT_SECONDS: float = 30.0

    # Phase 8: Failure Recovery & Exponential Backoff Retry Policy
    RECOVERY_MAX_RETRIES: int = 3
    RECOVERY_INITIAL_RETRY_DELAY_SECONDS: float = 2.0
    RECOVERY_BACKOFF_FACTOR: float = 2.0  # 2s, 4s, 8s...
    RECOVERY_MAX_RETRY_DELAY_SECONDS: float = 30.0

    # Phase 8: Circuit Breaker Configuration (RabbitMQ and external dependencies)
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 3
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT_SECONDS: float = 10.0
    CIRCUIT_BREAKER_HALF_OPEN_MAX_REQUESTS: int = 2

    # Phase 8: Failure Simulation & Testing Harness
    ENABLE_FAILURE_SIMULATION: bool = True

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @property
    def database_url(self) -> str:
        """Construct or return the primary PostgreSQL database connection URL."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def test_database_url(self) -> str:
        """Construct or return the test PostgreSQL database connection URL."""
        if self.TEST_DATABASE_URL:
            return self.TEST_DATABASE_URL
        return (
            f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.TEST_DB_NAME}"
        )

    def get_branch_database_url(self, branch_id: str, is_test: bool = False) -> str:
        """Return dedicated connection URL for a specific branch."""
        b_id = branch_id.upper()
        if b_id == "BLR001":
            if self.BLR_DATABASE_URL:
                return self.BLR_DATABASE_URL
            db_name = self.BLR_TEST_DB_NAME if is_test else self.BLR_DB_NAME
            return f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{db_name}"
        elif b_id == "CHE001":
            if self.CHE_DATABASE_URL:
                return self.CHE_DATABASE_URL
            db_name = self.CHE_TEST_DB_NAME if is_test else self.CHE_DB_NAME
            return f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{db_name}"
        elif b_id == "HYD001":
            if self.HYD_DATABASE_URL:
                return self.HYD_DATABASE_URL
            db_name = self.HYD_TEST_DB_NAME if is_test else self.HYD_DB_NAME
            return f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{db_name}"
        return self.test_database_url if is_test else self.database_url

    @property
    def safe_database_info(self) -> dict:
        """Return safe database connection details with credentials stripped."""
        return {
            "host": self.DB_HOST,
            "port": self.DB_PORT,
            "database": self.DB_NAME,
            "user": self.DB_USER,
        }

    @property
    def rabbitmq_url(self) -> str:
        """Construct or return the AMQP connection URL."""
        if self.RABBITMQ_URL:
            return self.RABBITMQ_URL
        vhost = self.RABBITMQ_VHOST.lstrip("/")
        vhost_part = f"/{vhost}" if vhost else "/"
        return f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}{vhost_part}"

    @property
    def safe_rabbitmq_info(self) -> dict:
        """Return safe RabbitMQ connection details without credentials."""
        return {
            "host": self.RABBITMQ_HOST,
            "port": self.RABBITMQ_PORT,
            "vhost": self.RABBITMQ_VHOST,
            "exchange": self.RABBITMQ_EXCHANGE,
            "dlx": self.RABBITMQ_DLX_EXCHANGE,
        }


@lru_cache()
def get_settings() -> Settings:
    """Retrieve cached application settings instance."""
    return Settings()


settings = get_settings()


def validate_security_config(cfg: Settings = settings) -> List[str]:
    """
    Validates security settings at application startup.
    Ensures that production mode does not silently use development secrets.
    """
    warnings: List[str] = []
    default_dev_jwt = "bankflow-secure-jwt-secret-key-development-environment-2026-simulation-change-in-prod"
    default_dev_enc = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"

    if cfg.ENVIRONMENT.lower() == "production":
        if cfg.JWT_SECRET_KEY == default_dev_jwt:
            raise ValueError("FATAL: Default development JWT_SECRET_KEY cannot be used in production environment.")
        if len(cfg.JWT_SECRET_KEY) < 32:
            raise ValueError("FATAL: JWT_SECRET_KEY must be at least 32 characters in production.")
        if cfg.DATA_ENCRYPTION_KEY == default_dev_enc:
            raise ValueError("FATAL: Default development DATA_ENCRYPTION_KEY cannot be used in production environment.")
        if len(cfg.DATA_ENCRYPTION_KEY) < 32:
            raise ValueError("FATAL: DATA_ENCRYPTION_KEY must provide at least 256 bits of entropy in production.")
        if cfg.FEDERATION_GATEWAY_SECRET == "bankflow-fed-gateway-root-secret-2026-key":
            raise ValueError("FATAL: Default development FEDERATION_GATEWAY_SECRET cannot be used in production environment.")
    else:
        if cfg.JWT_SECRET_KEY == default_dev_jwt:
            warnings.append("Using development JWT_SECRET_KEY. Do not deploy to production with this key.")
        if cfg.DATA_ENCRYPTION_KEY == default_dev_enc:
            warnings.append("Using development DATA_ENCRYPTION_KEY. Do not deploy to production with this key.")
        if cfg.FEDERATION_GATEWAY_SECRET == "bankflow-fed-gateway-root-secret-2026-key":
            warnings.append("Using development FEDERATION_GATEWAY_SECRET. Configure unique gateway secret for production.")

    return warnings

