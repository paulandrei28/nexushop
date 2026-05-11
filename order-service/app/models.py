import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Numeric, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_email = Column(String(255), nullable=False)
    status = Column(
        String(20), nullable=False, default="pending"
    )  # pending, confirmed, failed, cancelled
    total_amount = Column(Numeric(10, 2), nullable=False, default=0)
    failure_reason = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    items = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "customer_email": self.customer_email,
            "status": self.status,
            "total_amount": float(self.total_amount),
            "failure_reason": self.failure_reason,
            "items": [item.to_dict() for item in self.items],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=False)
    product_id = Column(String(36), nullable=False)
    product_name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)

    order = relationship("Order", back_populates="items")

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "quantity": self.quantity,
            "unit_price": float(self.unit_price),
            "subtotal": float(self.unit_price * self.quantity),
        }
