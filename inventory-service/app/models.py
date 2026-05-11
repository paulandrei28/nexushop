import uuid
from datetime import datetime, timezone

from app.extensions import db


class InventoryItem(db.Model):
    __tablename__ = "inventory"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    product_id = db.Column(db.String(36), nullable=False, unique=True, index=True)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    reserved = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    @property
    def available(self) -> int:
        return self.quantity - self.reserved

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "reserved": self.reserved,
            "available": self.available,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class Reservation(db.Model):
    __tablename__ = "reservations"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    order_id = db.Column(db.String(36), nullable=False, index=True)
    product_id = db.Column(db.String(36), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(
        db.String(20), nullable=False, default="reserved"
    )  # reserved, confirmed, released
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }
