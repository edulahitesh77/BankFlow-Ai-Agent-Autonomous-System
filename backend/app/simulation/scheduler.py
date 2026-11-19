"""
BankFlow AI - Workload-Aware Scheduler
Implements modular assignment policies for selecting Request and Service Agents.
"""

from typing import List, Optional
from app.models.request import Request, ServiceType
from app.agents.request_agent import RequestAgent
from app.agents.service_agent import ServiceAgent


class LeastLoadedPolicy:
    """
    Selects the least-loaded available agent.
    Tie-breaking uses stable alphabetical agent_code.
    """

    @staticmethod
    def select_request_agent(
        available_agents: List[RequestAgent],
        request: Optional[Request] = None,
    ) -> Optional[RequestAgent]:
        """Selects the RequestAgent with the lowest completed work count."""
        idle_agents = [a for a in available_agents if a.is_available]
        if not idle_agents:
            return None

        # Sort by (completed_work_count, agent_code)
        idle_agents.sort(key=lambda a: (a.completed_work_count, a.agent_code))
        return idle_agents[0]

    @staticmethod
    def select_service_agent(
        available_agents: List[ServiceAgent],
        service_type: ServiceType,
    ) -> Optional[ServiceAgent]:
        """Selects an available ServiceAgent matching the required skill."""
        compatible_idle = [
            a for a in available_agents
            if a.is_available and a.can_handle_service(service_type)
        ]
        if not compatible_idle:
            return None

        compatible_idle.sort(key=lambda a: (a.completed_work_count, a.agent_code))
        return compatible_idle[0]


class WorkloadScheduler:
    """Configurable scheduler managing assignment policies."""

    def __init__(self, policy=LeastLoadedPolicy):
        self.policy = policy

    def dispatch_request_agent(
        self,
        available_agents: List[RequestAgent],
        request: Request,
    ) -> Optional[RequestAgent]:
        return self.policy.select_request_agent(available_agents, request)

    def dispatch_service_agent(
        self,
        available_agents: List[ServiceAgent],
        service_type: ServiceType,
    ) -> Optional[ServiceAgent]:
        return self.policy.select_service_agent(available_agents, service_type)
