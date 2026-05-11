import logging

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import InventoryItem, Reservation

logger = logging.getLogger(__name__)

inventory_bp = Blueprint("inventory", __name__, url_prefix="/inventory")


@inventory_bp.route("", methods=["GET"])
def list_inventory():
    """List all inventory items."""
    items = InventoryItem.query.order_by(InventoryItem.updated_at.desc()).all()
    return jsonify({"items": [item.to_dict() for item in items]}), 200


@inventory_bp.route("/<product_id>", methods=["GET"])
def get_inventory(product_id):
    """Get inventory for a specific product."""
    item = InventoryItem.query.filter_by(product_id=product_id).first()
    if not item:
        return jsonify({"error": "Inventory not found for product"}), 404
    return jsonify(item.to_dict()), 200


@inventory_bp.route("", methods=["POST"])
def create_inventory():
    """Create or update inventory for a product."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    product_id = data.get("product_id")
    quantity = data.get("quantity")

    if not product_id:
        return jsonify({"error": "product_id is required"}), 400
    if quantity is None or not isinstance(quantity, int) or quantity < 0:
        return jsonify({"error": "quantity must be a non-negative integer"}), 400

    item = InventoryItem.query.filter_by(product_id=product_id).first()
    if item:
        item.quantity = quantity
    else:
        item = InventoryItem(product_id=product_id, quantity=quantity)
        db.session.add(item)

    db.session.commit()
    logger.info("Inventory set for product %s: qty=%d", product_id, quantity)
    return jsonify(item.to_dict()), 201


@inventory_bp.route("/<product_id>/add", methods=["POST"])
def add_stock(product_id):
    """Add stock to an existing inventory item."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    quantity = data.get("quantity")
    if quantity is None or not isinstance(quantity, int) or quantity <= 0:
        return jsonify({"error": "quantity must be a positive integer"}), 400

    item = InventoryItem.query.filter_by(product_id=product_id).first()
    if not item:
        return jsonify({"error": "Inventory not found for product"}), 404

    item.quantity += quantity
    db.session.commit()
    logger.info("Added %d stock for product %s", quantity, product_id)
    return jsonify(item.to_dict()), 200


@inventory_bp.route("/<product_id>/reserve", methods=["POST"])
def reserve_stock(product_id):
    """Reserve stock for an order (HTTP endpoint for direct calls)."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    quantity = data.get("quantity")
    order_id = data.get("order_id")

    if not order_id:
        return jsonify({"error": "order_id is required"}), 400
    if quantity is None or not isinstance(quantity, int) or quantity <= 0:
        return jsonify({"error": "quantity must be a positive integer"}), 400

    item = InventoryItem.query.filter_by(product_id=product_id).first()
    if not item:
        return jsonify({"error": "Inventory not found for product"}), 404

    if item.available < quantity:
        return (
            jsonify(
                {
                    "error": "Insufficient stock",
                    "available": item.available,
                    "requested": quantity,
                }
            ),
            409,
        )

    item.reserved += quantity
    reservation = Reservation(
        order_id=order_id,
        product_id=product_id,
        quantity=quantity,
        status="reserved",
    )
    db.session.add(reservation)
    db.session.commit()

    logger.info(
        "Reserved %d of product %s for order %s",
        quantity,
        product_id,
        order_id,
    )
    return jsonify(reservation.to_dict()), 200


@inventory_bp.route("/reservations/<order_id>/confirm", methods=["POST"])
def confirm_reservation(order_id):
    """Confirm reservations for an order (deduct from stock)."""
    reservations = Reservation.query.filter_by(
        order_id=order_id, status="reserved"
    ).all()
    if not reservations:
        return jsonify({"error": "No reservations found for order"}), 404

    for res in reservations:
        item = InventoryItem.query.filter_by(product_id=res.product_id).first()
        if item:
            item.quantity -= res.quantity
            item.reserved -= res.quantity
        res.status = "confirmed"

    db.session.commit()
    logger.info("Confirmed reservations for order %s", order_id)
    return jsonify({"message": "Reservations confirmed", "order_id": order_id}), 200


@inventory_bp.route("/reservations/<order_id>/release", methods=["POST"])
def release_reservation(order_id):
    """Release reservations for a failed/cancelled order."""
    reservations = Reservation.query.filter_by(
        order_id=order_id, status="reserved"
    ).all()
    if not reservations:
        return jsonify({"error": "No reservations found for order"}), 404

    for res in reservations:
        item = InventoryItem.query.filter_by(product_id=res.product_id).first()
        if item:
            item.reserved -= res.quantity
        res.status = "released"

    db.session.commit()
    logger.info("Released reservations for order %s", order_id)
    return jsonify({"message": "Reservations released", "order_id": order_id}), 200
