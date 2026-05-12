import os


class Settings:
    PRODUCT_SERVICE_URL: str = os.environ.get(
        "PRODUCT_SERVICE_URL", "http://localhost:8001"
    )
    ORDER_SERVICE_URL: str = os.environ.get(
        "ORDER_SERVICE_URL", "http://localhost:8002"
    )
    INVENTORY_SERVICE_URL: str = os.environ.get(
        "INVENTORY_SERVICE_URL", "http://localhost:8003"
    )
    USER_SERVICE_URL: str = os.environ.get("USER_SERVICE_URL", "http://localhost:8005")
    REDIS_URL: str = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    JWT_SECRET: str = os.environ.get("JWT_SECRET", "change-me-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = int(os.environ.get("JWT_EXPIRY_MINUTES", "60"))
    RATE_LIMIT_REQUESTS: int = int(os.environ.get("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW: int = int(os.environ.get("RATE_LIMIT_WINDOW", "60"))
    SERVICE_NAME: str = os.environ.get("SERVICE_NAME", "gateway")
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")


settings = Settings()
