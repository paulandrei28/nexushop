import logging

from flask import Blueprint, jsonify, request

from app.repository import ProductRepository

logger = logging.getLogger(__name__)

products_bp = Blueprint("products", __name__, url_prefix="/products")


@products_bp.route("", methods=["GET"])
def list_products():
    """List products with optional filtering and pagination."""
    category = request.args.get("category")
    search = request.args.get("search")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    # Clamp per_page to prevent abuse
    per_page = min(per_page, 100)

    result = ProductRepository.get_all(
        category=category,
        search=search,
        page=page,
        per_page=per_page,
    )
    return jsonify(result), 200


@products_bp.route("/<product_id>", methods=["GET"])
def get_product(product_id):
    """Get a single product by ID."""
    product = ProductRepository.get_by_id(product_id)
    if not product or not product.is_active:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(product.to_dict()), 200


@products_bp.route("", methods=["POST"])
def create_product():
    """Create a new product."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    errors = _validate_product_data(data)
    if errors:
        return jsonify({"errors": errors}), 400

    product = ProductRepository.create(data)
    logger.info("Product created: %s", product.id)
    return jsonify(product.to_dict()), 201


@products_bp.route("/<product_id>", methods=["PUT"])
def update_product(product_id):
    """Update an existing product."""
    product = ProductRepository.get_by_id(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    if "price" in data:
        try:
            price = float(data["price"])
            if price < 0:
                return jsonify({"errors": ["Price must be non-negative"]}), 400
        except (ValueError, TypeError):
            return jsonify({"errors": ["Price must be a number"]}), 400

    product = ProductRepository.update(product, data)
    logger.info("Product updated: %s", product.id)
    return jsonify(product.to_dict()), 200


@products_bp.route("/<product_id>", methods=["DELETE"])
def delete_product(product_id):
    """Soft-delete a product."""
    product = ProductRepository.get_by_id(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    ProductRepository.delete(product)
    logger.info("Product deleted (soft): %s", product_id)
    return jsonify({"message": "Product deleted"}), 200


@products_bp.route("/categories", methods=["GET"])
def list_categories():
    """List all product categories."""
    categories = ProductRepository.get_categories()
    return jsonify({"categories": categories}), 200


def _validate_product_data(data: dict) -> list:
    """Validate required fields for product creation."""
    errors = []
    if not data.get("name"):
        errors.append("Name is required")
    if not data.get("category"):
        errors.append("Category is required")
    if "price" not in data:
        errors.append("Price is required")
    else:
        try:
            price = float(data["price"])
            if price < 0:
                errors.append("Price must be non-negative")
        except (ValueError, TypeError):
            errors.append("Price must be a number")
    return errors
