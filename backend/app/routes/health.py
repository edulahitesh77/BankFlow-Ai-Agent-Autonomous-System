"""
BankFlow AI - Health and Root Routes
Provides root metadata, health inspection, and database connectivity diagnostic endpoints.
"""

from fastapi import APIRouter, status, Response
from app.config import settings
from app.database import check_db_connectivity
from app.schemas import ProjectInfoResponse, HealthResponse, DatabaseHealthResponse

router = APIRouter(tags=["System & Diagnostics"])


@router.get(
    "/",
    response_model=ProjectInfoResponse,
    status_code=status.HTTP_200_OK,
    summary="Project Information",
    description="Returns high-level project metadata, version, and primary API links.",
)
def get_root_info() -> ProjectInfoResponse:
    """Return high-level project information and available endpoints."""
    return ProjectInfoResponse(
        name=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Intelligent Multi-Agent Banking Service Automation System",
        phase="Phase 1: Project Setup and Database Implementation",
        status="operational",
        docs_url="/docs",
        endpoints={
            "root": "/",
            "health": "/health",
            "database_health": "/health/database",
            "swagger_docs": "/docs",
            "redoc": "/redoc",
        },
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Backend Health Check",
    description="Returns backend service status and deployment environment.",
)
def get_health() -> HealthResponse:
    """Check whether the FastAPI backend is alive and functioning."""
    return HealthResponse(
        status="healthy",
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
    )


@router.get(
    "/health/database",
    response_model=DatabaseHealthResponse,
    summary="Database Connectivity Check",
    description="Tests PostgreSQL database reachability without exposing sensitive credentials.",
)
def get_database_health(response: Response) -> DatabaseHealthResponse:
    """
    Check if the PostgreSQL database is reachable.
    Returns HTTP 200 if connected, or HTTP 503 if unreachable.
    """
    db_status = check_db_connectivity()
    if not db_status.get("reachable"):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return DatabaseHealthResponse(
        status=db_status.get("status", "error"),
        reachable=db_status.get("reachable", False),
        database=db_status.get("database"),
        host=db_status.get("host"),
        port=db_status.get("port"),
        error=db_status.get("error"),
    )
