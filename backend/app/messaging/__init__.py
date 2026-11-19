"""
BankFlow AI - Messaging Package
Centralized exports for message broker connection, topology, schema, publisher, and consumer.
"""

from app.messaging.connection import connection_manager, RabbitMQConnectionManager
from app.messaging.message_schema import StandardBankingMessage, BankingEventType
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
    ALL_QUEUES,
    get_routing_key,
)
from app.messaging.exchanges import declare_exchanges
from app.messaging.queues import declare_queues_and_bindings, inspect_queues_status
from app.messaging.publisher import MessagePublisher
from app.messaging.consumer import MessageConsumer
from app.messaging.duplicate_protection import DuplicateProtectionService, DuplicateMessageError
from app.messaging.retry import RetryPolicyService
from app.messaging.dead_letter import DeadLetterService
from app.messaging.broker_service import BrokerService

__all__ = [
    "connection_manager",
    "RabbitMQConnectionManager",
    "StandardBankingMessage",
    "BankingEventType",
    "MAIN_EXCHANGE",
    "DEAD_LETTER_EXCHANGE",
    "QUEUE_INTAKE",
    "QUEUE_REQUEST_AGENT",
    "QUEUE_VERIFICATION",
    "QUEUE_SERVICE",
    "QUEUE_SUPERVISOR",
    "QUEUE_NOTIFICATION",
    "QUEUE_DEAD_LETTER",
    "ALL_QUEUES",
    "get_routing_key",
    "declare_exchanges",
    "declare_queues_and_bindings",
    "inspect_queues_status",
    "MessagePublisher",
    "MessageConsumer",
    "DuplicateProtectionService",
    "DuplicateMessageError",
    "RetryPolicyService",
    "DeadLetterService",
    "BrokerService",
]
