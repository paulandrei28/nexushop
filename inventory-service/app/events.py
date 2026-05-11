import json
import logging
import threading

from app.extensions import db
from app.models import InventoryItem, Reservation

logger = logging.getLogger(__name__)


def handle_order_created(message: dict, app):
    """Handle order.created event -- reserve stock for all items."""
    order_id = message.get("order_id")
    items = message.get("items", [])

    logger.info("Processing order.created for order %s", order_id)

    with app.app_context():
        reservations = []
        failed = False

        for item in items:
            product_id = item["product_id"]
            quantity = item["quantity"]

            inv = InventoryItem.query.filter_by(product_id=product_id).first()
            if not inv or inv.available < quantity:
                failed = True
                logger.warning(
                    "Insufficient stock for product %s (need %d, available %d)",
                    product_id,
                    quantity,
                    inv.available if inv else 0,
                )
                break

            inv.reserved += quantity
            reservation = Reservation(
                order_id=order_id,
                product_id=product_id,
                quantity=quantity,
                status="reserved",
            )
            db.session.add(reservation)
            reservations.append(reservation)

        if failed:
            db.session.rollback()
            # Release any partial reservations
            return {
                "event": "inventory.failed",
                "order_id": order_id,
                "reason": "insufficient_stock",
            }

        db.session.commit()
        logger.info(
            "Reserved stock for order %s (%d items)", order_id, len(reservations)
        )
        return {
            "event": "inventory.reserved",
            "order_id": order_id,
            "reservations": [r.to_dict() for r in reservations],
        }


def handle_order_confirmed(message: dict, app):
    """Handle order.confirmed event -- deduct stock permanently."""
    order_id = message.get("order_id")

    with app.app_context():
        reservations = Reservation.query.filter_by(
            order_id=order_id, status="reserved"
        ).all()

        for res in reservations:
            inv = InventoryItem.query.filter_by(product_id=res.product_id).first()
            if inv:
                inv.quantity -= res.quantity
                inv.reserved -= res.quantity
            res.status = "confirmed"

        db.session.commit()
        logger.info("Confirmed stock deduction for order %s", order_id)


def handle_order_failed(message: dict, app):
    """Handle order.failed event -- release reserved stock."""
    order_id = message.get("order_id")

    with app.app_context():
        reservations = Reservation.query.filter_by(
            order_id=order_id, status="reserved"
        ).all()

        for res in reservations:
            inv = InventoryItem.query.filter_by(product_id=res.product_id).first()
            if inv:
                inv.reserved -= res.quantity
            res.status = "released"

        db.session.commit()
        logger.info("Released stock for failed order %s", order_id)


def start_consumer(app, rabbitmq_connection):
    """Start the RabbitMQ consumer in a background thread."""
    from shared.messaging import (
        EXCHANGE_ORDERS,
        ROUTING_KEY_ORDER_CREATED,
        ROUTING_KEY_ORDER_CONFIRMED,
        ROUTING_KEY_ORDER_FAILED,
        EXCHANGE_INVENTORY,
        ROUTING_KEY_INVENTORY_RESERVED,
        ROUTING_KEY_INVENTORY_FAILED,
    )

    def _consume():
        try:
            rmq = rabbitmq_connection
            rmq.declare_exchange(EXCHANGE_ORDERS)
            rmq.declare_exchange(EXCHANGE_INVENTORY)

            # Declare queues
            rmq.declare_queue(
                queue="inventory.order_created",
                exchange=EXCHANGE_ORDERS,
                routing_key=ROUTING_KEY_ORDER_CREATED,
            )
            rmq.declare_queue(
                queue="inventory.order_confirmed",
                exchange=EXCHANGE_ORDERS,
                routing_key=ROUTING_KEY_ORDER_CONFIRMED,
            )
            rmq.declare_queue(
                queue="inventory.order_failed",
                exchange=EXCHANGE_ORDERS,
                routing_key=ROUTING_KEY_ORDER_FAILED,
            )

            channel = rmq.connect()
            channel.basic_qos(prefetch_count=1)

            def on_order_created(ch, method, properties, body):
                try:
                    message = json.loads(body)
                    result = handle_order_created(message, app)

                    # Publish result back
                    if result["event"] == "inventory.reserved":
                        rmq.publish(
                            EXCHANGE_INVENTORY,
                            ROUTING_KEY_INVENTORY_RESERVED,
                            result,
                        )
                    else:
                        rmq.publish(
                            EXCHANGE_INVENTORY,
                            ROUTING_KEY_INVENTORY_FAILED,
                            result,
                        )

                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except Exception:
                    logger.exception("Error processing order.created")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

            def on_order_confirmed(ch, method, properties, body):
                try:
                    message = json.loads(body)
                    handle_order_confirmed(message, app)
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except Exception:
                    logger.exception("Error processing order.confirmed")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

            def on_order_failed(ch, method, properties, body):
                try:
                    message = json.loads(body)
                    handle_order_failed(message, app)
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except Exception:
                    logger.exception("Error processing order.failed")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

            channel.basic_consume(
                queue="inventory.order_created", on_message_callback=on_order_created
            )
            channel.basic_consume(
                queue="inventory.order_confirmed",
                on_message_callback=on_order_confirmed,
            )
            channel.basic_consume(
                queue="inventory.order_failed", on_message_callback=on_order_failed
            )

            logger.info("Inventory consumer started, waiting for messages...")
            channel.start_consuming()
        except Exception:
            logger.exception("Consumer crashed, will not auto-restart in this version")

    thread = threading.Thread(target=_consume, daemon=True)
    thread.start()
    logger.info("Inventory consumer thread started")
