import os


class Settings:
    RABBITMQ_URL: str = os.environ.get(
        "RABBITMQ_URL", "amqp://guest:guest@localhost:5672/"
    )
    SMTP_HOST: str = os.environ.get("SMTP_HOST", "localhost")
    SMTP_PORT: int = int(os.environ.get("SMTP_PORT", "1025"))
    FROM_EMAIL: str = os.environ.get("FROM_EMAIL", "noreply@nexushop.local")
    SERVICE_NAME: str = os.environ.get("SERVICE_NAME", "notification-service")
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")


settings = Settings()
