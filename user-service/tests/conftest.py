import os
import sys

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET"] = "test-secret"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest

from app.main import create_app
from app.extensions import db as _db


@pytest.fixture
def app():
    app = create_app()
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def registered_user(client):
    """Register a user and return (response_data, password)."""
    password = "securepass123"
    resp = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": password,
            "name": "Test User",
        },
    )
    return resp.get_json(), password
