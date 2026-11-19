"""
BankFlow AI - Agent Registry
Synchronizes Mesa in-memory multi-agent instances with PostgreSQL database records.
"""

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.agent import Agent as DBAgent, AgentType
from app.models.request import Request
from app.agents.base_agent import BaseBankingAgent


class AgentRegistry:
    """Manages persistence and lookup of agent instances between Mesa and PostgreSQL."""

    @staticmethod
    def sync_agents_to_database(db: Session, agents: List[BaseBankingAgent]) -> None:
        """
        Persists in-memory Mesa agent status, workload counters, and active request
        associations into the PostgreSQL `agents` table.
        """
        for agent in agents:
            db_agent = db.query(DBAgent).filter(DBAgent.agent_code == agent.agent_code).first()

            # Resolve integer request id if current_request_id is a synthetic string code
            req_int_id = None
            if agent.current_request_id:
                req = db.query(Request).filter(
                    Request.request_id == agent.current_request_id
                ).first()
                if req:
                    req_int_id = req.id

            health_status_val = (
                agent.health_status.value
                if hasattr(agent.health_status, "value")
                else str(agent.health_status)
            )

            if not db_agent:
                db_agent = DBAgent(
                    agent_code=agent.agent_code,
                    agent_type=agent.agent_type,
                    availability_status=agent.availability_status,
                    processing_status=agent.processing_status,
                    current_request_id=req_int_id,
                    branch_id=agent.branch_id,
                    completed_work_count=agent.completed_work_count,
                    last_active_at=agent.last_active_at,
                    health_status=health_status_val,
                    last_heartbeat_at=getattr(agent, "last_heartbeat_at", None),
                    failed_work_count=getattr(agent, "failed_work_count", 0),
                    retry_count=getattr(agent, "retry_count", 0),
                    total_processing_time_ms=getattr(agent, "total_processing_time_ms", 0.0),
                    last_error_message=getattr(agent, "last_error_message", None),
                    is_paused=getattr(agent, "is_paused", False),
                )
                db.add(db_agent)
                db.flush()
            else:
                db_agent.availability_status = agent.availability_status
                db_agent.processing_status = agent.processing_status
                db_agent.current_request_id = req_int_id
                db_agent.completed_work_count = agent.completed_work_count
                db_agent.last_active_at = agent.last_active_at
                db_agent.health_status = health_status_val
                db_agent.last_heartbeat_at = getattr(agent, "last_heartbeat_at", None)
                db_agent.failed_work_count = getattr(agent, "failed_work_count", 0)
                db_agent.retry_count = getattr(agent, "retry_count", 0)
                db_agent.total_processing_time_ms = getattr(agent, "total_processing_time_ms", 0.0)
                db_agent.last_error_message = getattr(agent, "last_error_message", None)
                db_agent.is_paused = getattr(agent, "is_paused", False)

            # Cache the database primary key ID on the Mesa agent instance
            agent.db_id = db_agent.id

        db.commit()
