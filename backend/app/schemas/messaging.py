"""
BankFlow AI - Messaging API Schemas
Pydantic v2 schemas for broker status, queue depths, communication history, and dead letter operations.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class BrokerStatusResponse(BaseModel):
    """RabbitMQ broker connection and topology health details."""
    broker_status: str
    connected: bool
    host: Optional[str] = None
    port: Optional[int] = None
    vhost: Optional[str] = None
    main_exchange: str
    dlx_exchange: str


class QueueStatusItem(BaseModel):
    """Queue depth and active consumer metrics."""
    queue_name: str
    message_count: int
    consumer_count: int
    status: str
    error: Optional[str] = None


class AgentEventItem(BaseModel):
    """Record of an individual communication event exchanged across agents."""
    id: int
    event_id: str
    request_id: str
    agent_id: str
    event_type: str
    previous_state: Optional[str] = None
    new_state: Optional[str] = None
    timestamp: Optional[str] = None
    reason_code: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None


class EventHistoryResponse(BaseModel):
    """Paginated list of multi-agent communication events."""
    total: int
    page: int
    page_size: int
    items: List[AgentEventItem]


class DeadLetterItem(BaseModel):
    """Failed message routed to dead-letter queue."""
    id: int
    message_id: str
    request_id: Optional[str] = None
    event_type: str
    consumer_name: str
    processing_status: str
    retry_count: int
    received_at: Optional[str] = None
    processed_at: Optional[str] = None
    error_message: Optional[str] = None
    payload_snapshot: Optional[Dict[str, Any]] = None


class DeadLetterListResponse(BaseModel):
    """Paginated dead letter messages."""
    total: int
    page: int
    page_size: int
    items: List[DeadLetterItem]


class RetryMessageResponse(BaseModel):
    """Response returned when a dead-letter message is manually re-queued."""
    message_id: str
    status: str
    retried_by: str
    routing_key: str
    timestamp: str


class CommunicationStatisticsResponse(BaseModel):
    """Aggregate broker throughput and idempotency metrics."""
    total_messages_published: int
    total_messages_consumed: int
    successfully_processed: int
    duplicate_messages_caught: int
    retried_messages: int
    dead_letter_messages: int


class AgentCommunicationMetric(BaseModel):
    """Communication statistics broken down by individual agent."""
    agent_id: int
    agent_code: str
    agent_type: str
    availability_status: str
    processing_status: str
    messages_published: int
    tasks_consumed: int
    completed_work_count: int
    last_active_at: Optional[str] = None
