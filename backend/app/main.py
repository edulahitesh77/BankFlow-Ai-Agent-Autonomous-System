"""
BankFlow AI - Intelligent Multi-Agent Banking Service Automation System
Main FastAPI Application Entrypoint
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request as FastAPIRequest, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings, validate_security_config
from app.routes import (
    health_router,
    auth_router,
    customer_router,
    bank_router,
    agents_router,
    simulation_router,
    messaging_router,
    admin_router,
    recovery_router,
    federation_router,
    visualizer_router,
)
from app.messaging.connection import connection_manager
from app.messaging.queues import declare_queues_and_bindings

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("bankflow_ai")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown routines."""
    logger.info("Initializing %s v%s...", settings.APP_NAME, settings.APP_VERSION)
    logger.info("Environment: %s", settings.ENVIRONMENT)

    # Validate security configuration at startup
    sec_warnings = validate_security_config(settings)
    for warn in sec_warnings:
        logger.warning("Security Warning: %s", warn)

    try:
        declare_queues_and_bindings()
        logger.info("RabbitMQ messaging topology declared successfully.")
    except Exception as e:
        logger.warning("RabbitMQ topology startup initialization deferred: %s", str(e))
    yield
    logger.info("Shutting down %s...", settings.APP_NAME)
    connection_manager.close_all()


def create_application() -> FastAPI:
    """Factory creating and configuring the primary FastAPI application instance."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "BankFlow AI is an educational banking service automation system "
            "simulating intelligent multi-agent request classification, verification, "
            "and service processing."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Configure CORS middleware for local frontend and multi-origin development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # HTTP Security Middleware: Request Size Enforcement & Hardened Security Headers
    @app.middleware("http")
    async def security_middleware(request: FastAPIRequest, call_next):
        # 1. Enforce payload size limit
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.MAX_REQUEST_BODY_SIZE_BYTES:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={
                    "status": "error",
                    "detail": f"Request body exceeds maximum allowed size of {settings.MAX_REQUEST_BODY_SIZE_BYTES} bytes.",
                },
            )

        # 2. Process request through pipeline
        response = await call_next(request)

        # 3. Apply defensive security headers
        if settings.ENABLE_SECURITY_HEADERS:
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response

    # Register API Routers
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(customer_router)
    app.include_router(bank_router)
    app.include_router(agents_router)
    app.include_router(simulation_router)
    app.include_router(messaging_router)
    app.include_router(admin_router)
    app.include_router(recovery_router)
    app.include_router(federation_router)
    app.include_router(visualizer_router)

    # Top-level WebSocket monitoring route
    from app.routes.agents import websocket_agent_monitoring
    app.add_api_websocket_route("/ws/agents/monitoring", websocket_agent_monitoring)

    # Global Exception Handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: FastAPIRequest, exc: Exception):
        logger.error("Unhandled exception processing request %s: %s", request.url.path, str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": "An internal server error occurred while processing the request.",
                "path": request.url.path,
            },
        )

    return app


app = create_application()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
