"""
BankFlow AI - Supervisor Agent
Monitors multi-agent health, tracks worker availability, detects bottlenecks,
audits message broker traffic, and broadcasts supervisory alerts over RabbitMQ.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import mesa
from sqlalchemy.orm import Session

from app.models.agent import AgentType, Agent
from app.agents.base_agent import BaseBankingAgent
from app.messaging.message_schema import StandardBankingMessage, BankingEventType
from app.messaging.publisher import MessagePublisher

logger = logging.getLogger("bankflow_ai.agents.supervisor")


class SupervisorAgent(BaseBankingAgent):
    """
    Supervisor Agent responsible for system oversight, workload tracking,
    message broker monitoring, and broadcast of supervisory alerts.
    """

    def __init__(
        self,
        model: mesa.Model,
        agent_code: str = "AGT-SUPERVISOR-01",
    ):
        super().__init__(model, agent_code, AgentType.SUPERVISOR)

    def generate_health_report(self) -> Dict[str, Any]:
        """
        Gathers operational telemetry from the simulation model and agent pool.
        """
        request_agents = [
            a for a in self.model.agents if getattr(a, "agent_type", None) == AgentType.REQUEST
        ]
        service_agents = [
            a for a in self.model.agents if getattr(a, "agent_type", None) == AgentType.SERVICE
        ]

        available_request_agents = sum(1 for a in request_agents if a.is_available)
        busy_request_agents = sum(1 for a in request_agents if not a.is_available)

        available_service_agents = sum(1 for a in service_agents if a.is_available)
        busy_service_agents = sum(1 for a in service_agents if not a.is_available)

        total_completed = sum(getattr(a, "completed_work_count", 0) for a in self.model.agents)
        healthy_count = sum(1 for a in self.model.agents if getattr(a, "health_status", None) in ("HEALTHY", "IDLE"))
        unresponsive_count = sum(1 for a in self.model.agents if getattr(a, "health_status", None) == "UNRESPONSIVE")
        failed_count = sum(1 for a in self.model.agents if getattr(a, "health_status", None) == "FAILED")

        return {
            "supervisor_code": self.agent_code,
            "status": "OPERATIONAL",
            "total_agents": len(self.model.agents),
            "healthy_agents": healthy_count,
            "unresponsive_agents": unresponsive_count,
            "failed_agents": failed_count,
            "request_agents": {
                "total": len(request_agents),
                "available": available_request_agents,
                "busy": busy_request_agents,
            },
            "service_agents": {
                "total": len(service_agents),
                "available": available_service_agents,
                "busy": busy_service_agents,
            },
            "total_requests_processed": total_completed,
            "system_load": (
                round(busy_request_agents / len(request_agents), 2)
                if len(request_agents) > 0
                else 0.0
            ),
        }

    def publish_alert(
        self,
        db: Session,
        alert_type: str,
        message_text: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> StandardBankingMessage:
        """Publishes a SUPERVISOR_ALERT message to the supervisor topic on RabbitMQ."""
        msg = StandardBankingMessage(
            request_id=f"ALERT-{alert_type}",
            request_version=0,
            sender_agent_id=self.agent_code,
            receiver_agent_id="BankStaffOperations",
            event_type=BankingEventType.SUPERVISOR_ALERT,
            reason_code=alert_type,
            payload={
                "alert_type": alert_type,
                "message": message_text,
                "details": details or {},
                "emitted_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        logger.warning("Supervisor published alert [%s]: %s", alert_type, message_text)
        return MessagePublisher.publish_event(db=db, message=msg, routing_key="supervisor.alert")

    def monitor_agent_heartbeats(
        self,
        db: Session,
        stale_threshold_seconds: int = 120,
    ) -> List[Dict[str, Any]]:
        """
        Inspects agent heartbeat freshness in the database.
        Emits alerts for agents whose activity exceeds the stale threshold.
        """
        now = datetime.now(timezone.utc)
        agents = db.query(Agent).all()
        alerts_generated = []

        for agt in agents:
            if agt.last_active_at:
                # Ensure timezone aware comparison
                last_active = agt.last_active_at
                if last_active.tzinfo is None:
                    last_active = last_active.replace(tzinfo=timezone.utc)
                elapsed = (now - last_active).total_seconds()
                if elapsed > stale_threshold_seconds:
                    alert = {
                        "agent_code": agt.agent_code,
                        "agent_type": agt.agent_type.value if hasattr(agt.agent_type, "value") else str(agt.agent_type),
                        "elapsed_seconds": round(elapsed, 1),
                        "status": "STALE_HEARTBEAT",
                    }
                    alerts_generated.append(alert)
                    self.publish_alert(
                        db=db,
                        alert_type="STALE_AGENT_HEARTBEAT",
                        message_text=f"Agent '{agt.agent_code}' has not reported in {round(elapsed, 1)} seconds.",
                        details=alert,
                    )

        return alerts_generated

    def inspect_and_recover(self, db: Session) -> Dict[str, Any]:
        """
        Executes Phase 8 health inspection and automated recovery of abandoned tasks.
        """
        from app.services.recovery_service import AgentRecoveryService
        return AgentRecoveryService.inspect_agents_health(db=db, sim_model=self.model)
