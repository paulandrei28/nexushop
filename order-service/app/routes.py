import logging
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Order, OrderItem
from app.events import publish_order_created

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orders", tags=["orders"])


# ── Request/Response schemas ──────────────────────────────────────


class OrderItemCreate(BaseModel):
    product_id: str
    product_name: str
    quantity: int
    unit_price: float

    @field_validator("quantity")
    @classmethod
    def quantity_positive(cls, v):
        if v <= 0:
            raise ValueError("quantity must be positive")
        return v

    @field_validator("unit_price")
    @classmethod
    def price_non_negative(cls, v):
        if v < 0:
            raise ValueError("unit_price must be non-negative")
        return v


class OrderCreate(BaseModel):
    customer_email: str
    items: List[OrderItemCreate]

    @field_validator("items")
    @classmethod
    def items_not_empty(cls, v):
        if not v:
            raise ValueError("Order must have at least one item")
        return v


# ── Endpoints ─────────────────────────────────────────────────────


@router.get("")
def list_orders(
    status: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
    db: Session = Depends(get_db),
):
    """List orders with optional status filter."""
    query = db.query(Order)
    if status:
        query = query.filter(Order.status == status)

    total = query.count()
    orders = (
        query.order_by(Order.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return {
        "items": [o.to_dict() for o in orders],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.get("/{order_id}")
def get_order(order_id: str, db: Session = Depends(get_db)):
    """Get a single order by ID."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order.to_dict()


@router.post("", status_code=201)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    """Create a new order and trigger the saga flow."""
    # Calculate total
    total = sum(Decimal(str(item.unit_price)) * item.quantity for item in payload.items)

    # Create order
    order = Order(
        customer_email=payload.customer_email,
        status="pending",
        total_amount=total,
    )
    db.add(order)
    db.flush()  # Get the ID

    # Create order items
    for item in payload.items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            product_name=item.product_name,
            quantity=item.quantity,
            unit_price=item.unit_price,
        )
        db.add(order_item)

    db.commit()
    db.refresh(order)

    # Publish order.created event to trigger saga
    publish_order_created(order)

    logger.info("Order created: %s (total: %s)", order.id, total)
    return order.to_dict()


@router.post("/{order_id}/cancel")
def cancel_order(order_id: str, db: Session = Depends(get_db)):
    """Cancel a pending order."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status not in ("pending", "confirmed"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel order with status '{order.status}'",
        )

    order.status = "cancelled"
    db.commit()

    logger.info("Order cancelled: %s", order_id)
    return order.to_dict()
