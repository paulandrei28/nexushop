import json
import logging
import threading

import pika

from app.config import settings
from app.email_sender import send_order_confirmed_email, send_order_failed_email

logger = logging.getLogger(__name__)


def handle_order_confirmed(message: dict):
    """Handle order.confirmed -- send confirmation email."""
    order_id = message.get("order_id")
    customer_email = message.get("customer_email")

    if not customer_email:
        logger.warning("No customer_email in order.confirmed message for %s", order_id)
        return

    logger.info(
        "Sending confirmation email for order %s to %s", order_id, customer_email
    )
    send_order_confirmed_email(order_id, customer_email)


def handle_order_failed(message: dict):
    """Handle order.failed -- send failure notification."""
    order_id = message.get("order_id")
    customer_email = message.get("customer_email")
    reason = message.get("reason", "Unknown error")

    if not customer_email:
        logger.warning("No customer_email in order.failed message for %s", order_id)
        return

    logger.info("Sending failure email for order %s to %s", order_id, customer_email)
    send_order_failed_email(order_id, customer_email, reason)


def start_consumer():
    """Start the RabbitMQ consumer for notification events."""

    def _consume():
        import time

        max_retries = 5
        for attempt in range(max_retries):
            try:
                params = pika.URLParameters(settings.RABBITMQ_URL)
                params.heartbeat = 600
                connection = pika.BlockingConnection(params)
                channel = connection.channel()

                # Declare exchange
                channel.exchange_declare(
                    exchange="orders", exchange_type="topic", durable=True
                )

                # Queue for order.confirmed
                channel.queue_declare(
                    queue="notifications.order_confirmed", durable=True
                )
                channel.queue_bind(
                    queue="notifications.order_confirmed",
                    exchange="orders",
                    routing_key="order.confirmed",
                )

                # Queue for order.failed
                channel.queue_declare(queue="notifications.order_failed", durable=True)
                channel.queue_bind(
                    queue="notifications.order_failed",
                    exchange="orders",
                    routing_key="order.failed",
                )

                channel.basic_qos(prefetch_count=1)

                def on_order_confirmed(ch, method, properties, body):
                    try:
                        message = json.loads(body)
                        handle_order_confirmed(message)
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                    except Exception:
                        logger.exception("Error handling order.confirmed notification")
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

                def on_order_failed(ch, method, properties, body):
                    try:
                        message = json.loads(body)
                        handle_order_failed(message)
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                    except Exception:
                        logger.exception("Error handling order.failed notification")
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

                channel.basic_consume(
                    queue="notifications.order_confirmed",
                    on_message_callback=on_order_confirmed,
                )
                channel.basic_consume(
                    queue="notifications.order_failed",
                    on_message_callback=on_order_failed,
                )

                logger.info("Notification consumer started, waiting for messages...")
                channel.start_consuming()
                break  # Should not reach here unless consumer stops
            except pika.exceptions.AMQPConnectionError:
                wait = min(2**attempt, 30)
                logger.warning(
                    "RabbitMQ not ready (attempt %d/%d), retrying in %ds",
                    attempt + 1,
                    max_retries,
                    wait,
                )
                time.sleep(wait)
        else:
            logger.error("Failed to connect to RabbitMQ after %d attempts", max_retries)

    thread = threading.Thread(target=_consume, daemon=True)
    thread.start()
    logger.info("Notification consumer thread started")
