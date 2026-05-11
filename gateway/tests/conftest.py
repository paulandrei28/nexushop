import os

os.environ["JWT_SECRET"] = "test-secret"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["PRODUCT_SERVICE_URL"] = "http://product-service:8000"
os.environ["ORDER_SERVICE_URL"] = "http://order-service:8000"
os.environ["INVENTORY_SERVICE_URL"] = "http://inventory-service:8000"

import pytest
from unittest.mock import AsyncMock, patch

from httpx import ASGITransport, AsyncClient

from app.main import app
from app.rate_limiter import _redis_pool


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """Async test client with Redis mocked out."""
    # Disable Redis for tests (rate limiting will be skipped)
    import app.rate_limiter as rl_mod

    rl_mod._redis_pool = None

    # Reset circuit breakers between tests
    from app.service_proxy import product_cb, order_cb, inventory_cb

    for cb in (product_cb, order_cb, inventory_cb):
        cb._fail_counter = 0
        cb._state = cb._state.__class__("closed")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
