"""
BankFlow AI - RabbitMQ Connection Manager
Centralized connection pooling, health inspection, and channel provisioning for AMQP broker.
Supports both synchronous (pika) and asynchronous (aio-pika) operations without leaking connections.
"""

import logging
import threading
from typing import Optional, Dict, Any
import pika
from pika.adapters.blocking_connection import BlockingChannel
import aio_pika

from app.config import settings

logger = logging.getLogger("bankflow_ai.messaging.connection")


class RabbitMQConnectionManager:
    """
    Singleton connection manager handling resilient RabbitMQ connections.
    Avoids opening new TCP connections per message and reuses authenticated channels.
    """
    _instance: Optional["RabbitMQConnectionManager"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "RabbitMQConnectionManager":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._sync_connection = None
                cls._instance._sync_channel = None
                cls._instance._async_connection = None
                cls._instance._async_channel = None
                cls._instance._conn_lock = threading.RLock()
            return cls._instance

    def get_sync_connection(self) -> pika.BlockingConnection:
        """Retrieves or establishes a resilient synchronous pika BlockingConnection."""
        with self._conn_lock:
            if self._sync_connection is None or self._sync_connection.is_closed:
                logger.info("Establishing synchronous RabbitMQ connection to %s:%s", settings.RABBITMQ_HOST, settings.RABBITMQ_PORT)
                parameters = pika.ConnectionParameters(
                    host=settings.RABBITMQ_HOST,
                    port=settings.RABBITMQ_PORT,
                    virtual_host=settings.RABBITMQ_VHOST,
                    credentials=pika.PlainCredentials(settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD),
                    heartbeat=60,
                    blocked_connection_timeout=30,
                )
                self._sync_connection = pika.BlockingConnection(parameters)
                self._sync_channel = None
            return self._sync_connection

    def get_sync_channel(self) -> BlockingChannel:
        """Retrieves or creates a reusable synchronous channel with publisher confirms enabled."""
        with self._conn_lock:
            conn = self.get_sync_connection()
            if self._sync_channel is None or self._sync_channel.is_closed:
                self._sync_channel = conn.channel()
                self._sync_channel.confirm_delivery()
                self._sync_channel.basic_qos(prefetch_count=settings.RABBITMQ_PREFETCH_COUNT)
            return self._sync_channel

    async def get_async_connection(self) -> aio_pika.abc.AbstractRobustConnection:
        """Retrieves or establishes a resilient asynchronous aio-pika robust connection."""
        if self._async_connection is None or self._async_connection.is_closed:
            logger.info("Establishing asynchronous aio-pika connection to %s", settings.rabbitmq_url)
            self._async_connection = await aio_pika.connect_robust(
                settings.rabbitmq_url,
                timeout=10.0,
            )
            self._async_channel = None
        return self._async_connection

    async def get_async_channel(self) -> aio_pika.abc.AbstractRobustChannel:
        """Retrieves or creates a reusable asynchronous robust channel."""
        conn = await self.get_async_connection()
        if self._async_channel is None or self._async_channel.is_closed:
            self._async_channel = await conn.channel(publisher_confirms=True)
            await self._async_channel.set_qos(prefetch_count=settings.RABBITMQ_PREFETCH_COUNT)
        return self._async_channel

    def check_health(self) -> Dict[str, Any]:
        """Performs a lightweight ping against RabbitMQ to assess broker availability."""
        try:
            conn = self.get_sync_connection()
            is_open = conn.is_open
            return {
                "connected": is_open,
                "host": settings.RABBITMQ_HOST,
                "port": settings.RABBITMQ_PORT,
                "vhost": settings.RABBITMQ_VHOST,
                "status": "HEALTHY" if is_open else "DISCONNECTED",
            }
        except Exception as e:
            logger.warning("RabbitMQ health check failed: %s", str(e))
            return {
                "connected": False,
                "host": settings.RABBITMQ_HOST,
                "port": settings.RABBITMQ_PORT,
                "vhost": settings.RABBITMQ_VHOST,
                "status": "UNREACHABLE",
                "error": str(e),
            }

    def close_all(self) -> None:
        """Closes open connections gracefully on application shutdown."""
        with self._conn_lock:
            try:
                if self._sync_channel and not self._sync_channel.is_closed:
                    self._sync_channel.close()
                if self._sync_connection and not self._sync_connection.is_closed:
                    self._sync_connection.close()
            except Exception as e:
                logger.error("Error closing synchronous RabbitMQ connection: %s", str(e))
            finally:
                self._sync_channel = None
                self._sync_connection = None


# Global singleton instance
connection_manager = RabbitMQConnectionManager()
