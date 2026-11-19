"""
BankFlow AI - Messaging Routing & Topology Constants
Defines RabbitMQ exchange names, durable queues, and topic routing key conventions.
"""

from app.messaging.message_schema import BankingEventType

# Central Exchange Names
MAIN_EXCHANGE = "bankflow.events"
DEAD_LETTER_EXCHANGE = "bankflow.dlx"

# Durable Queue Names
QUEUE_INTAKE = "bankflow.intake.q"
QUEUE_REQUEST_AGENT = "bankflow.request_agent.q"
QUEUE_VERIFICATION = "bankflow.verification.q"
QUEUE_SERVICE = "bankflow.service.q"
QUEUE_SUPERVISOR = "bankflow.supervisor.q"
QUEUE_NOTIFICATION = "bankflow.notification.q"
QUEUE_DEAD_LETTER = "bankflow.dlq"

ALL_QUEUES = [
    QUEUE_INTAKE,
    QUEUE_REQUEST_AGENT,
    QUEUE_VERIFICATION,
    QUEUE_SERVICE,
    QUEUE_SUPERVISOR,
    QUEUE_NOTIFICATION,
    QUEUE_DEAD_LETTER,
]

# Topic Routing Keys mapped to event types
EVENT_ROUTING_KEYS = {
    BankingEventType.REQUEST_CREATED: "request.created",
    BankingEventType.REQUEST_CLASSIFIED: "request.classified",
    BankingEventType.REQUEST_ASSIGNED: "request.assigned",
    BankingEventType.REQUEST_ACCEPTED: "request.accepted",
    BankingEventType.VERIFICATION_COMPLETED: "request.verified",
    BankingEventType.VERIFICATION_FAILED: "request.rejected",
    BankingEventType.HUMAN_REVIEW_REQUIRED: "request.human_review",
    BankingEventType.REQUEST_NEEDS_CORRECTION: "request.needs_correction",
    BankingEventType.SERVICE_STARTED: "service.started",
    BankingEventType.SERVICE_COMPLETED: "service.completed",
    BankingEventType.SERVICE_FAILED: "service.failed",
    BankingEventType.AGENT_AVAILABLE: "agent.available",
    BankingEventType.AGENT_UNAVAILABLE: "agent.unavailable",
    BankingEventType.AGENT_HEARTBEAT: "agent.heartbeat",
    BankingEventType.SUPERVISOR_ALERT: "supervisor.alert",
}

# Queue to Topic Binding Patterns
QUEUE_BINDINGS = {
    QUEUE_INTAKE: [
        "request.created",
        "request.needs_correction",  # Resubmission from customer
    ],
    QUEUE_REQUEST_AGENT: [
        "request.classified",
        "request.assigned",
    ],
    QUEUE_VERIFICATION: [
        "request.accepted",
    ],
    QUEUE_SERVICE: [
        "request.verified",
    ],
    QUEUE_SUPERVISOR: [
        "request.*",
        "service.*",
        "agent.*",
        "supervisor.*",
    ],
    QUEUE_NOTIFICATION: [
        "request.created",
        "request.needs_correction",
        "request.human_review",
        "service.completed",
        "request.rejected",
    ],
    QUEUE_DEAD_LETTER: [
        "#",  # Dead letter exchange catches all rejected/expired events
    ],
}


def get_routing_key(event_type: BankingEventType) -> str:
    """Returns the AMQP topic routing key for a given banking event."""
    return EVENT_ROUTING_KEYS.get(event_type, "request.general")
