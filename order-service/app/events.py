import json
import logging
import threading
from typing import Optional

import pika

from app.config import settings

logger = logging.getLogger(__name__)

# Global RabbitMQ connection (initialized on startup)
_rmq_channel: Optional[pika.channel.Channel] = None
_rmq_connection: Optional[pika.BlockingConnection] = None


def get_rmq_channel():
    """Get or create a RabbitMQ channel for publishing."""
    global _rmq_channel, _rmq_connection
    if _rmq_channel and _rmq_channel.is_open:
        return _rmq_channel

    import time

    max_retries = 5
    for attempt in range(max_retries):
        try:
            params = pika.URLParameters(settings.RABBITMQ_URL)
            params.heartbeat = 600
            _rmq_connection = pika.BlockingConnection(params)
            _rmq_channel = _rmq_connection.channel()
            _rmq_channel.exchange_declare(
                exchange="orders", exchange_type="topic", durable=True
            )
            _rmq_channel.exchange_declare(
                exchange="inventory", exchange_type="topic", durable=True
            )
            logger.info("RabbitMQ publisher connected")
            return _rmq_channel
        except pika.exceptions.AMQPConnectionError:
            wait = min(2**attempt, 30)
            logger.warning(
                "RabbitMQ connection failed (attempt %d/%d), retrying in %ds",
                attempt + 1,
                max_retries,
                wait,
            )
            time.sleep(wait)

    raise ConnectionError("Failed to connect to RabbitMQ for publishing")


def publish_order_created(order):
    """Publish order.created event to RabbitMQ."""
    message = {
        "event": "order.created",
        "order_id": order.id,
        "customer_email": order.customer_email,
        "total_amount": float(order.total_amount),
        "items": [
            {
                "product_id": item.product_id,
                "product_name": item.product_name,
                "quantity": item.quantity,
                "unit_price": float(item.unit_price),
            }
            for item in order.items
        ],
    }

    try:
        channel = get_rmq_channel()
        channel.basic_publish(
            exchange="orders",
            routing_key="order.created",
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type="application/json",
            ),
        )
        logger.info("Published order.created for order %s", order.id)
    except Exception:
        logger.exception("Failed to publish order.created for order %s", order.id)


def publish_order_confirmed(order_id: str, customer_email: str):
    """Publish order.confirmed event."""
    message = {
        "event": "order.confirmed",
        "order_id": order_id,
        "customer_email": customer_email,
    }
    try:
        channel = get_rmq_channel()
        channel.basic_publish(
            exchange="orders",
            routing_key="order.confirmed",
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type="application/json",
            ),
        )
        logger.info("Published order.confirmed for order %s", order_id)
    except Exception:
        logger.exception("Failed to publish order.confirmed for %s", order_id)


def publish_order_failed(order_id: str, customer_email: str, reason: str):
    """Publish order.failed event."""
    message = {
        "event": "order.failed",
        "order_id": order_id,
        "customer_email": customer_email,
        "reason": reason,
    }
    try:
        channel = get_rmq_channel()
        channel.basic_publish(
            exchange="orders",
            routing_key="order.failed",
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type="application/json",
            ),
        )
        logger.info("Published order.failed for order %s", order_id)
    except Exception:
        logger.exception("Failed to publish order.failed for %s", order_id)


def handle_inventory_reserved(message: dict):
    """Handle inventory.reserved event -- confirm the order."""
    from app.database import SessionLocal
    from app.models import Order

    order_id = message.get("order_id")
    logger.info("Inventory reserved for order %s, confirming...", order_id)

    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if order and order.status == "pending":
            order.status = "confirmed"
            db.commit()
            publish_order_confirmed(order.id, order.customer_email)
            logger.info("Order %s confirmed", order_id)
    except Exception:
        db.rollback()
        logger.exception("Error confirming order %s", order_id)
    finally:
        db.close()


def handle_inventory_failed(message: dict):
    """Handle inventory.failed event -- mark order as failed."""
    from app.database import SessionLocal
    from app.models import Order

    order_id = message.get("order_id")
    reason = message.get("reason", "unknown")
    logger.info("Inventory failed for order %s: %s", order_id, reason)

    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if order and order.status == "pending":
            order.status = "failed"
            order.failure_reason = reason
            db.commit()
            publish_order_failed(order.id, order.customer_email, reason)
            logger.info("Order %s marked as failed", order_id)
    except Exception:
        db.rollback()
        logger.exception("Error failing order %s", order_id)
    finally:
        db.close()


def start_consumer():
    """Start the RabbitMQ consumer for inventory responses."""

    def _consume():
        try:
            params = pika.URLParameters(settings.RABBITMQ_URL)
            params.heartbeat = 600
            connection = pika.BlockingConnection(params)
            channel = connection.channel()

            channel.exchange_declare(
                exchange="inventory", exchange_type="topic", durable=True
            )

            # Queue for inventory.reserved
            channel.queue_declare(queue="orders.inventory_reserved", durable=True)
            channel.queue_bind(
                queue="orders.inventory_reserved",
                exchange="inventory",
                routing_key="inventory.reserved",
            )

            # Queue for inventory.failed
            channel.queue_declare(queue="orders.inventory_failed", durable=True)
            channel.queue_bind(
                queue="orders.inventory_failed",
                exchange="inventory",
                routing_key="inventory.failed",
            )

            channel.basic_qos(prefetch_count=1)

            def on_inventory_reserved(ch, method, properties, body):
                try:
                    message = json.loads(body)
                    handle_inventory_reserved(message)
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except Exception:
                    logger.exception("Error handling inventory.reserved")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

            def on_inventory_failed(ch, method, properties, body):
                try:
                    message = json.loads(body)
                    handle_inventory_failed(message)
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except Exception:
                    logger.exception("Error handling inventory.failed")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

            channel.basic_consume(
                queue="orders.inventory_reserved",
                on_message_callback=on_inventory_reserved,
            )
            channel.basic_consume(
                queue="orders.inventory_failed",
                on_message_callback=on_inventory_failed,
            )

            logger.info("Order consumer started, waiting for inventory responses...")
            channel.start_consuming()
        except Exception:
            logger.exception("Order consumer crashed")

    thread = threading.Thread(target=_consume, daemon=True)
    thread.start()
    logger.info("Order consumer thread started")
