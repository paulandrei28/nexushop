import json
import logging
import time
from functools import wraps
from typing import Any, Callable, Optional

import pika

logger = logging.getLogger(__name__)


class RabbitMQConnection:
    """Manages RabbitMQ connection with automatic reconnection."""

    def __init__(self, url: str, service_name: str = "unknown"):
        self.url = url
        self.service_name = service_name
        self._connection: Optional[pika.BlockingConnection] = None
        self._channel: Optional[pika.channel.Channel] = None

    def connect(self) -> pika.channel.Channel:
        if self._connection and self._connection.is_open:
            return self._channel

        max_retries = 5
        for attempt in range(max_retries):
            try:
                params = pika.URLParameters(self.url)
                params.heartbeat = 600
                params.blocked_connection_timeout = 300
                self._connection = pika.BlockingConnection(params)
                self._channel = self._connection.channel()
                self._channel.confirm_delivery()
                logger.info(
                    "Connected to RabbitMQ (attempt %d)",
                    attempt + 1,
                )
                return self._channel
            except pika.exceptions.AMQPConnectionError:
                wait = min(2**attempt, 30)
                logger.warning(
                    "RabbitMQ connection failed, retrying in %ds (attempt %d/%d)",
                    wait,
                    attempt + 1,
                    max_retries,
                )
                time.sleep(wait)

        raise ConnectionError(
            f"[{self.service_name}] Failed to connect to RabbitMQ after {max_retries} attempts"
        )

    def close(self):
        if self._connection and self._connection.is_open:
            self._connection.close()
            logger.info("RabbitMQ connection closed")

    def declare_exchange(self, exchange: str, exchange_type: str = "topic"):
        channel = self.connect()
        channel.exchange_declare(
            exchange=exchange,
            exchange_type=exchange_type,
            durable=True,
        )

    def declare_queue(
        self,
        queue: str,
        exchange: str,
        routing_key: str,
        dlx_exchange: Optional[str] = None,
    ):
        channel = self.connect()
        arguments = {}
        if dlx_exchange:
            arguments["x-dead-letter-exchange"] = dlx_exchange

        channel.queue_declare(queue=queue, durable=True, arguments=arguments)
        channel.queue_bind(queue=queue, exchange=exchange, routing_key=routing_key)

    def publish(self, exchange: str, routing_key: str, message: dict):
        channel = self.connect()
        channel.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type="application/json",
            ),
        )
        logger.info(
            "Published message to %s with key %s",
            exchange,
            routing_key,
        )

    def consume(
        self,
        queue: str,
        callback: Callable[[dict], None],
        auto_ack: bool = False,
    ):
        channel = self.connect()
        channel.basic_qos(prefetch_count=1)

        def _wrapper(ch, method, properties, body):
            try:
                message = json.loads(body)
                callback(message)
                if not auto_ack:
                    ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception:
                logger.exception(
                    "Error processing message from %s",
                    queue,
                )
                if not auto_ack:
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        channel.basic_consume(queue=queue, on_message_callback=_wrapper)
        logger.info(
            "Started consuming from %s",
            queue,
        )
        channel.start_consuming()


# Exchange and routing key constants
EXCHANGE_ORDERS = "orders"
EXCHANGE_INVENTORY = "inventory"
EXCHANGE_NOTIFICATIONS = "notifications"
EXCHANGE_DLX = "dlx"

ROUTING_KEY_ORDER_CREATED = "order.created"
ROUTING_KEY_ORDER_CONFIRMED = "order.confirmed"
ROUTING_KEY_ORDER_FAILED = "order.failed"
ROUTING_KEY_INVENTORY_RESERVED = "inventory.reserved"
ROUTING_KEY_INVENTORY_FAILED = "inventory.failed"
ROUTING_KEY_NOTIFICATION_SEND = "notification.send"
