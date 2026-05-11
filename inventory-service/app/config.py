import os


class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql://ecommerce:ecommerce_secret@localhost:5432/inventory_db",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    SERVICE_NAME = os.environ.get("SERVICE_NAME", "inventory-service")
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
