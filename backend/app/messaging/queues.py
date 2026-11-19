"""
BankFlow AI - Queue Declarations and Bindings
Configures durable agent queues with dead-letter exchange policies and topic routing bindings.
"""

import logging
from typing import Optional, Dict, Any, List
import pika
from pika.adapters.blocking_connection import BlockingChannel
from app.messaging.connection import connection_manager
from app.messaging.routing import (
    MAIN_EXCHANGE,
    DEAD_LETTER_EXCHANGE,
    QUEUE_DEAD_LETTER,
    QUEUE_BINDINGS,
    ALL_QUEUES,
)
from app.messaging.exchanges import declare_exchanges

logger = logging.getLogger("bankflow_ai.messaging.queues")


def declare_queues_and_bindings(channel: Optional[BlockingChannel] = None) -> None:
    """
    Declares all durable queues with dead-letter exchange forwarding arguments,
    and sets up topic routing key bindings.
    """
    ch = channel or connection_manager.get_sync_channel()

    # Ensure exchanges exist before declaring queues
    declare_exchanges(ch)

    # 1. Declare the Dead Letter Queue first
    logger.info("Declaring dead-letter queue '%s'...", QUEUE_DEAD_LETTER)
    ch.queue_declare(
        queue=QUEUE_DEAD_LETTER,
        durable=True,
        exclusive=False,
        auto_delete=False,
    )
    ch.queue_bind(
        queue=QUEUE_DEAD_LETTER,
        exchange=DEAD_LETTER_EXCHANGE,
        routing_key="#",
    )

    # 2. Declare Domain Agent Queues with DLX enabled
    dlx_args = {
        "x-dead-letter-exchange": DEAD_LETTER_EXCHANGE,
        "x-dead-letter-routing-key": "deadletter.unhandled",
    }

    for queue_name, binding_keys in QUEUE_BINDINGS.items():
        if queue_name == QUEUE_DEAD_LETTER:
            continue

        logger.info("Declaring durable queue '%s' with DLX policy...", queue_name)
        ch.queue_declare(
            queue=queue_name,
            durable=True,
            exclusive=False,
            auto_delete=False,
            arguments=dlx_args,
        )

        for key in binding_keys:
            logger.debug("Binding queue '%s' to exchange '%s' on key '%s'", queue_name, MAIN_EXCHANGE, key)
            ch.queue_bind(
                queue=queue_name,
                exchange=MAIN_EXCHANGE,
                routing_key=key,
            )


def inspect_queues_status(channel: Optional[BlockingChannel] = None) -> List[Dict[str, Any]]:
    """Inspects queue depths, message counts, and consumer counts."""
    ch = channel or connection_manager.get_sync_channel()
    declare_queues_and_bindings(ch)

    results = []
    for q_name in ALL_QUEUES:
        try:
            # Passive declare returns (method, queue_name, message_count, consumer_count)
            res = ch.queue_declare(queue=q_name, passive=True)
            results.append({
                "queue_name": q_name,
                "message_count": res.method.message_count,
                "consumer_count": res.method.consumer_count,
                "status": "ACTIVE",
            })
        except Exception as e:
            results.append({
                "queue_name": q_name,
                "message_count": 0,
                "consumer_count": 0,
                "status": "ERROR",
                "error": str(e),
            })

    return results

