import os


class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql://ecommerce:ecommerce_secret@localhost:5432/users_db",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET = os.environ.get("JWT_SECRET", "change-me-in-production")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRY_MINUTES = int(os.environ.get("JWT_EXPIRY_MINUTES", "60"))
    SERVICE_NAME = os.environ.get("SERVICE_NAME", "user-service")
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
