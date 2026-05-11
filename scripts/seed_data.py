"""Seed the database with sample products."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.main import create_app
from app.extensions import db
from app.models import Product

PRODUCTS = [
    {
        "name": "Mechanical Keyboard",
        "description": "Cherry MX Blue switches, RGB backlit, full-size layout",
        "price": 89.99,
        "category": "Electronics",
        "image_url": "https://example.com/images/keyboard.jpg",
    },
    {
        "name": "Wireless Mouse",
        "description": "Ergonomic design, 4000 DPI, USB-C rechargeable",
        "price": 34.99,
        "category": "Electronics",
        "image_url": "https://example.com/images/mouse.jpg",
    },
    {
        "name": "USB-C Hub",
        "description": "7-in-1 hub with HDMI, USB 3.0, SD card reader",
        "price": 29.99,
        "category": "Electronics",
        "image_url": "https://example.com/images/hub.jpg",
    },
    {
        "name": "Standing Desk Mat",
        "description": "Anti-fatigue mat, 20x34 inches, ergonomic design",
        "price": 44.99,
        "category": "Office",
        "image_url": "https://example.com/images/mat.jpg",
    },
    {
        "name": "Monitor Arm",
        "description": "Gas spring mount, supports up to 32 inch displays",
        "price": 69.99,
        "category": "Office",
        "image_url": "https://example.com/images/monitor-arm.jpg",
    },
    {
        "name": "Noise Cancelling Headphones",
        "description": "Active noise cancelling, 30 hour battery, Bluetooth 5.3",
        "price": 149.99,
        "category": "Audio",
        "image_url": "https://example.com/images/headphones.jpg",
    },
    {
        "name": "Webcam HD 1080p",
        "description": "Auto-focus, built-in microphone, privacy shutter",
        "price": 54.99,
        "category": "Electronics",
        "image_url": "https://example.com/images/webcam.jpg",
    },
    {
        "name": "Desk Organizer",
        "description": "Bamboo desktop organizer with 5 compartments",
        "price": 24.99,
        "category": "Office",
        "image_url": "https://example.com/images/organizer.jpg",
    },
    {
        "name": "Portable SSD 1TB",
        "description": "USB 3.2, read speeds up to 1050 MB/s, shock resistant",
        "price": 89.99,
        "category": "Storage",
        "image_url": "https://example.com/images/ssd.jpg",
    },
    {
        "name": "Cable Management Kit",
        "description": "Velcro ties, cable clips, sleeve wrap - 120 piece set",
        "price": 14.99,
        "category": "Office",
        "image_url": "https://example.com/images/cables.jpg",
    },
]


def seed():
    app = create_app()
    with app.app_context():
        existing = Product.query.count()
        if existing > 0:
            print(f"Database already has {existing} products, skipping seed.")
            return

        for product_data in PRODUCTS:
            product = Product(**product_data)
            db.session.add(product)

        db.session.commit()
        print(f"Seeded {len(PRODUCTS)} products.")


if __name__ == "__main__":
    seed()
