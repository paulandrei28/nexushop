import os
import sys

import pytest

# Ensure shared is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.main import create_app
from app.extensions import db as _db
from app.config import Config


class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    TESTING = True
    SERVICE_NAME = "product-service-test"


@pytest.fixture(scope="session")
def app():
    app = create_app(config_class=TestConfig)
    yield app


@pytest.fixture(scope="function")
def db(app):
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.rollback()
        _db.drop_all()


@pytest.fixture(scope="function")
def client(app, db):
    with app.test_client() as client:
        yield client
