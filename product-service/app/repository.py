from typing import List, Optional

from sqlalchemy import or_

from app.extensions import db
from app.models import Product


class ProductRepository:
    """Data access layer for products."""

    @staticmethod
    def get_all(
        category: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
        active_only: bool = True,
    ) -> dict:
        query = Product.query

        if active_only:
            query = query.filter(Product.is_active.is_(True))

        if category:
            query = query.filter(Product.category == category)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Product.name.ilike(search_term),
                    Product.description.ilike(search_term),
                )
            )

        query = query.order_by(Product.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            "items": [p.to_dict() for p in pagination.items],
            "total": pagination.total,
            "page": pagination.page,
            "per_page": pagination.per_page,
            "pages": pagination.pages,
        }

    @staticmethod
    def get_by_id(product_id: str) -> Optional[Product]:
        return db.session.get(Product, product_id)

    @staticmethod
    def create(data: dict) -> Product:
        product = Product(
            name=data["name"],
            description=data.get("description"),
            price=data["price"],
            category=data["category"],
            image_url=data.get("image_url"),
        )
        db.session.add(product)
        db.session.commit()
        return product

    @staticmethod
    def update(product: Product, data: dict) -> Product:
        for field in (
            "name",
            "description",
            "price",
            "category",
            "image_url",
            "is_active",
        ):
            if field in data:
                setattr(product, field, data[field])
        db.session.commit()
        return product

    @staticmethod
    def delete(product: Product) -> None:
        product.is_active = False
        db.session.commit()

    @staticmethod
    def get_categories() -> List[str]:
        results = (
            db.session.query(Product.category)
            .filter(Product.is_active.is_(True))
            .distinct()
            .order_by(Product.category)
            .all()
        )
        return [r[0] for r in results]
