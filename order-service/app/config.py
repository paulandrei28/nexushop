import os


class Settings:
    DATABASE_URL: str = os.environ.get(
        "DATABASE_URL",
        "postgresql://ecommerce:ecommerce_secret@localhost:5432/orders_db",
    )
    RABBITMQ_URL: str = os.environ.get(
        "RABBITMQ_URL", "amqp://guest:guest@localhost:5672/"
    )
    PRODUCT_SERVICE_URL: str = os.environ.get(
        "PRODUCT_SERVICE_URL", "http://localhost:8001"
    )
    INVENTORY_SERVICE_URL: str = os.environ.get(
        "INVENTORY_SERVICE_URL", "http://localhost:8003"
    )
    SERVICE_NAME: str = os.environ.get("SERVICE_NAME", "order-service")
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")


settings = Settings()
