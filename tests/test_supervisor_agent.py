"""
BankFlow AI - Supervisor Agent Tests
Tests system health telemetry, worker availability monitoring, and load metrics calculation.
"""

import sys
import os
import pytest

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.models.agent import AgentType
from app.simulation.model import BankingSimulationModel
from app.agents.supervisor_agent import SupervisorAgent


def test_supervisor_initialization():
    """Verify SupervisorAgent initializes correctly with operational status."""
    model = BankingSimulationModel()
    supervisor = model.supervisor_agent

    assert supervisor is not None
    assert supervisor.agent_type == AgentType.SUPERVISOR
    assert supervisor.agent_code == "AGT-SUPERVISOR-01"
    assert supervisor.is_available is True


def test_supervisor_health_report_generation():
    """Verify SupervisorAgent computes aggregated multi-agent metrics."""
    model = BankingSimulationModel()
    supervisor = model.supervisor_agent

    report = supervisor.generate_health_report()

    assert report["supervisor_code"] == "AGT-SUPERVISOR-01"
    assert report["status"] == "OPERATIONAL"
    assert report["total_agents"] >= 8  # Intake + Verif + 3 Request + 4 Service + Supervisor
    assert report["request_agents"]["total"] == 3
    assert report["request_agents"]["available"] == 3
    assert report["request_agents"]["busy"] == 0
    assert report["service_agents"]["total"] == 4
    assert report["system_load"] == 0.0


def test_supervisor_load_calculation_with_busy_agents():
    """Verify SupervisorAgent recalculates system load when worker agents become busy."""
    model = BankingSimulationModel()
    supervisor = model.supervisor_agent
    req_agents = model.get_request_agents()

    # Mark 2 request agents as busy
    req_agents[0].assign_request("REQ-TEST-A")
    req_agents[1].assign_request("REQ-TEST-B")

    report = supervisor.generate_health_report()

    assert report["request_agents"]["available"] == 1
    assert report["request_agents"]["busy"] == 2
    # 2 busy out of 3 = 0.67
    assert report["system_load"] == 0.67
