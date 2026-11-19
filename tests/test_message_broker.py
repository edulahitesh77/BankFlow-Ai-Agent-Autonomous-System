"""
BankFlow AI - Message Broker Tests
Tests RabbitMQ connection, topology declaration, message publishing with confirms,
and manual consumer acknowledgements.
"""

import sys
import os
import pytest
from sqlalchemy.orm import Session

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.messaging.connection import connection_manager
from app.messaging.routing import (
    MAIN_EXCHANGE,
    DEAD_LETTER_EXCHANGE,
    QUEUE_INTAKE,
    QUEUE_REQUEST_AGENT,
    QUEUE_VERIFICATION,
    QUEUE_SERVICE,
    QUEUE_SUPERVISOR,
    QUEUE_NOTIFICATION,
    QUEUE_DEAD_LETTER,
)
from app.messaging.exchanges import declare_exchanges
from app.messaging.queues import declare_queues_and_bindings, inspect_queues_status
from app.messaging.message_schema import StandardBankingMessage, BankingEventType
from app.messaging.publisher import MessagePublisher
from app.messaging.consumer import MessageConsumer


def test_rabbitmq_connection_health():
    """Verify RabbitMQ broker connection manager is operational and healthy."""
    health = connection_manager.check_health()
    assert health["connected"] is True
    assert health["status"] == "HEALTHY"
    assert health["port"] == 5672


def test_topology_declaration_and_queue_inspection():
    """Verify exchanges and queues are declared with active status."""
    declare_exchanges()
    assert MAIN_EXCHANGE == "bankflow.events"
    assert DEAD_LETTER_EXCHANGE == "bankflow.dlx"

    declare_queues_and_bindings()
    queues = inspect_queues_status()

    queue_names = [q["queue_name"] for q in queues]
    assert QUEUE_INTAKE in queue_names
    assert QUEUE_REQUEST_AGENT in queue_names
    assert QUEUE_VERIFICATION in queue_names
    assert QUEUE_SERVICE in queue_names
    assert QUEUE_SUPERVISOR in queue_names
    assert QUEUE_NOTIFICATION in queue_names
    assert QUEUE_DEAD_LETTER in queue_names
    assert all(q["status"] == "ACTIVE" for q in queues)


def test_publish_and_consume_with_manual_ack(db_session: Session):
    """Verify publishing a persistent message and consuming it with manual ack."""
    declare_queues_and_bindings()
    try:
        connection_manager.get_sync_channel().queue_purge(QUEUE_INTAKE)
    except Exception:
        pass

    msg = StandardBankingMessage(
        request_id="REQ-BROKER-TEST-01",
        request_version=0,
        sender_agent_id="AGT-CUST-SIM-01",
        receiver_agent_id="AGT-INTAKE-01",
        event_type=BankingEventType.REQUEST_CREATED,
        payload={"service": "CHEQUE_BOOK", "leaves": 25},
    )

    # 1. Publish to main exchange
    published_msg = MessagePublisher.publish_event(
        db=db_session,
        message=msg,
        new_state="NEW",
    )
    assert published_msg.message_id == msg.message_id

    # 2. Consume from Intake Queue
    consumed_items = []

    def sample_handler(db, m):
        consumed_items.append(m)

    results = MessageConsumer.consume_batch(
        queue_name=QUEUE_INTAKE,
        consumer_name="AGT-INTAKE-01",
        handler=sample_handler,
        max_messages=1,
    )

    assert len(results) == 1
    assert results[0]["status"] == "PROCESSED"
    assert len(consumed_items) == 1
    assert consumed_items[0].request_id == "REQ-BROKER-TEST-01"

