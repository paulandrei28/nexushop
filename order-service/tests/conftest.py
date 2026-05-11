import os
import sys
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

# Override the database URL BEFORE importing app modules
os.environ["DATABASE_URL"] = "sqlite:///./test_orders.db"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_orders.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Patch RabbitMQ before importing app
with patch("app.events.start_consumer"), patch("app.events.get_rmq_channel"):
    # Now override the database module
    import app.database as db_module

    db_module.engine = engine
    db_module.SessionLocal = TestingSessionLocal

    from app.main import app
    from app.database import Base, get_db


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    with TestClient(app) as c:
        yield c
