"""
BankFlow AI - Broker Inspection & Messaging Service
Aggregates queue depths, broker health, communication timelines, and audit metrics for bank dashboards.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.messaging.connection import connection_manager
from app.messaging.queues import inspect_queues_status
from app.messaging.routing import MAIN_EXCHANGE, DEAD_LETTER_EXCHANGE
from app.models.agent_event import AgentEvent
from app.models.processed_message import ProcessedMessage
from app.models.delivery_attempt import MessageDeliveryAttempt
from app.models.agent import Agent

logger = logging.getLogger("bankflow_ai.messaging.broker_service")


class BrokerService:
    """Service providing operational inspection of RabbitMQ and communication history."""

    @staticmethod
    def get_broker_status() -> Dict[str, Any]:
        """Returns connection health and high-level topology summary."""
        health = connection_manager.check_health()
        return {
            "broker_status": health["status"],
            "connected": health["connected"],
            "host": health.get("host"),
            "port": health.get("port"),
            "vhost": health.get("vhost"),
            "main_exchange": MAIN_EXCHANGE,
            "dlx_exchange": DEAD_LETTER_EXCHANGE,
        }

    @staticmethod
    def get_queues_status() -> List[Dict[str, Any]]:
        """Inspects all durable queue depths and consumer attachments."""
        return inspect_queues_status()

    @staticmethod
    def get_events_history(
        db: Session,
        request_id: Optional[str] = None,
        event_type: Optional[str] = None,
        agent_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """Queries communication events stored in AgentEvents with filtering and pagination."""
        query = db.query(AgentEvent)

        if request_id:
            query = query.filter(AgentEvent.request_id.ilike(f"%{request_id}%"))
        if event_type and event_type != "ALL":
            query = query.filter(AgentEvent.event_type == event_type)
        if agent_id and agent_id != "ALL":
            query = query.filter(AgentEvent.agent_id == agent_id)

        total = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(desc(AgentEvent.timestamp)).offset(offset).limit(page_size).all()

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [
                {
                    "id": ev.id,
                    "event_id": ev.event_id,
                    "request_id": ev.request_id,
                    "agent_id": ev.agent_id,
                    "event_type": ev.event_type,
                    "previous_state": ev.previous_state,
                    "new_state": ev.new_state,
                    "timestamp": ev.timestamp.isoformat() if ev.timestamp else None,
                    "reason_code": ev.reason_code,
                    "payload": ev.payload,
                }
                for ev in items
            ],
        }

    @staticmethod
    def get_request_communication_timeline(
        db: Session,
        request_id: str,
    ) -> List[Dict[str, Any]]:
        """Retrieves full chronological exchange history for a single request."""
        events = (
            db.query(AgentEvent)
            .filter(AgentEvent.request_id == request_id)
            .order_by(AgentEvent.timestamp.asc())
            .all()
        )

        timeline = []
        for ev in events:
            timeline.append({
                "id": ev.id,
                "event_id": ev.event_id,
                "request_id": ev.request_id,
                "agent_id": ev.agent_id,
                "event_type": ev.event_type,
                "previous_state": ev.previous_state,
                "new_state": ev.new_state,
                "timestamp": ev.timestamp.isoformat() if ev.timestamp else None,
                "reason_code": ev.reason_code,
                "payload": ev.payload,
            })
        return timeline

    @staticmethod
    def get_communication_statistics(db: Session) -> Dict[str, Any]:
        """Computes aggregate communication throughput, duplicate catches, and error metrics."""
        total_published = db.query(func.count(AgentEvent.id)).scalar() or 0
        total_consumed = db.query(func.count(ProcessedMessage.id)).scalar() or 0
        successfully_processed = (
            db.query(func.count(ProcessedMessage.id))
            .filter(ProcessedMessage.processing_status.in_(["PROCESSED", "COMPLETED"]))
            .scalar() or 0
        )
        duplicates_caught = (
            db.query(func.count(MessageDeliveryAttempt.id))
            .filter(MessageDeliveryAttempt.delivery_status == "DUPLICATE_IGNORED")
            .scalar() or 0
        )
        retried_messages = (
            db.query(func.count(MessageDeliveryAttempt.id))
            .filter(MessageDeliveryAttempt.delivery_status == "RETRY")
            .scalar() or 0
        )
        dead_letters = (
            db.query(func.count(ProcessedMessage.id))
            .filter(ProcessedMessage.processing_status == "DEAD_LETTER")
            .scalar() or 0
        )

        return {
            "total_messages_published": total_published,
            "total_messages_consumed": total_consumed,
            "successfully_processed": successfully_processed,
            "duplicate_messages_caught": duplicates_caught,
            "retried_messages": retried_messages,
            "dead_letter_messages": dead_letters,
        }

    @staticmethod
    def get_agent_communication_metrics(db: Session) -> List[Dict[str, Any]]:
        """Calculates messages published and task counts per agent."""
        agents = db.query(Agent).all()
        if not agents:
            from app.simulation.model import BankingSimulationModel
            from app.simulation.agent_registry import AgentRegistry
            sim = BankingSimulationModel()
            AgentRegistry.sync_agents_to_database(db, list(sim.agents))
            agents = db.query(Agent).all()

        results = []

        for agt in agents:
            events_published = (
                db.query(func.count(AgentEvent.id))
                .filter(AgentEvent.agent_id == agt.agent_code)
                .scalar() or 0
            )
            tasks_processed = (
                db.query(func.count(ProcessedMessage.id))
                .filter(ProcessedMessage.consumer_name == agt.agent_code)
                .scalar() or 0
            )

            results.append({
                "agent_id": agt.id,
                "agent_code": agt.agent_code,
                "agent_type": agt.agent_type.value if hasattr(agt.agent_type, "value") else str(agt.agent_type),
                "availability_status": agt.availability_status,
                "processing_status": getattr(agt, "processing_status", "IDLE"),
                "messages_published": events_published,
                "tasks_consumed": tasks_processed,
                "completed_work_count": getattr(agt, "completed_work_count", 0),
                "last_active_at": agt.last_active_at.isoformat() if getattr(agt, "last_active_at", None) else None,
            })

        return results

