"""
BankFlow AI - Exchange Declarations
Declares durable topic exchanges and dead letter exchanges on the broker.
"""

import logging
from typing import Optional
import pika
from pika.adapters.blocking_connection import BlockingChannel
from app.messaging.connection import connection_manager
from app.messaging.routing import MAIN_EXCHANGE, DEAD_LETTER_EXCHANGE

logger = logging.getLogger("bankflow_ai.messaging.exchanges")


def declare_exchanges(channel: Optional[BlockingChannel] = None) -> None:
    """
    Declares the central banking topic exchange and the dead-letter exchange.
    Both exchanges are durable so topology survives broker restarts.
    """
    ch = channel or connection_manager.get_sync_channel()

    # 1. Main Topic Exchange for all banking events
    logger.info("Declaring topic exchange '%s'...", MAIN_EXCHANGE)
    ch.exchange_declare(
        exchange=MAIN_EXCHANGE,
        exchange_type="topic",
        durable=True,
        auto_delete=False,
    )

    # 2. Dead Letter Exchange (DLX) for unhandled, rejected, or expired messages
    logger.info("Declaring dead-letter topic exchange '%s'...", DEAD_LETTER_EXCHANGE)
    ch.exchange_declare(
        exchange=DEAD_LETTER_EXCHANGE,
        exchange_type="topic",
        durable=True,
        auto_delete=False,
    )
