"""
BankFlow AI - Routes Package
Exposes configured API routers for registration in the main application.
"""

from app.routes.health import router as health_router
from app.routes.auth import router as auth_router
from app.routes.customer import router as customer_router
from app.routes.bank import router as bank_router
from app.routes.agents import router as agents_router
from app.routes.simulation import router as simulation_router
from app.routes.messaging import router as messaging_router
from app.routes.admin import admin_router
from app.routes.recovery import recovery_router
from app.routes.federation import router as federation_router
from app.routes.visualizer import router as visualizer_router

__all__ = [
    "health_router",
    "auth_router",
    "customer_router",
    "bank_router",
    "agents_router",
    "simulation_router",
    "messaging_router",
    "admin_router",
    "recovery_router",
    "federation_router",
    "visualizer_router",
]
