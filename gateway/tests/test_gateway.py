import time
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.auth import create_token, decode_token


# ---- Health ----


@pytest.mark.anyio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"


@pytest.mark.anyio
async def test_ready(client):
    resp = await client.get("/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert "circuit_breakers" in data


# ---- Auth ----


@pytest.mark.anyio
async def test_login(client):
    resp = await client.post(
        "/auth/login",
        json={"email": "test@example.com", "user_id": "u1"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.anyio
async def test_login_missing_email(client):
    resp = await client.post("/auth/login", json={"user_id": "u1"})
    assert resp.status_code == 400


def test_create_and_decode_token():
    token = create_token("user-1", "a@b.com", "customer")
    claims = decode_token(token)
    assert claims["sub"] == "user-1"
    assert claims["email"] == "a@b.com"
    assert claims["role"] == "customer"


def test_decode_expired_token():
    import jwt as pyjwt

    payload = {
        "sub": "u1",
        "email": "a@b.com",
        "role": "customer",
        "iat": int(time.time()) - 7200,
        "exp": int(time.time()) - 3600,
    }
    token = pyjwt.encode(payload, "test-secret", algorithm="HS256")
    with pytest.raises(Exception):
        decode_token(token)


def test_decode_invalid_token():
    with pytest.raises(Exception):
        decode_token("not.a.valid.token")


# ---- Auth Middleware ----


@pytest.mark.anyio
async def test_public_get_products_no_auth(client):
    """GET /products should be public (no auth required)."""
    mock_resp = httpx.Response(200, json={"products": []})
    with patch(
        "app.service_proxy._forward_request",
        new_callable=AsyncMock,
        return_value=mock_resp,
    ):
        resp = await client.get("/products")
        assert resp.status_code == 200


@pytest.mark.anyio
async def test_protected_post_orders_requires_auth(client):
    """POST /orders should require authentication."""
    resp = await client.post("/orders", json={"items": []})
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_protected_endpoint_with_valid_token(client):
    """POST /orders with valid JWT should pass auth and proxy."""
    token = create_token("u1", "test@example.com")
    mock_resp = httpx.Response(201, json={"id": "order-1"})
    with patch(
        "app.service_proxy._forward_request",
        new_callable=AsyncMock,
        return_value=mock_resp,
    ):
        resp = await client.post(
            "/orders",
            json={"customer_email": "test@example.com", "items": []},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201


# ---- Auth /me endpoint ----


@pytest.mark.anyio
async def test_auth_me_with_token(client):
    token = create_token("u1", "test@example.com", "admin")
    resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["sub"] == "u1"
    assert data["role"] == "admin"


@pytest.mark.anyio
async def test_auth_me_without_token(client):
    resp = await client.get("/auth/me")
    assert resp.status_code == 401


# ---- Proxy / Routing ----


@pytest.mark.anyio
async def test_unknown_route_requires_auth(client):
    """Unknown routes behind auth should return 401."""
    resp = await client.get("/nonexistent")
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_unknown_route_404_with_auth(client):
    """Unknown routes with valid auth should return 404."""
    token = create_token("u1", "test@example.com")
    resp = await client.get(
        "/nonexistent",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_proxy_forwards_to_product_service(client):
    mock_resp = httpx.Response(200, json={"id": "p1", "name": "Widget"})
    with patch(
        "app.service_proxy._forward_request",
        new_callable=AsyncMock,
        return_value=mock_resp,
    ):
        resp = await client.get("/products/p1")
        assert resp.status_code == 200


@pytest.mark.anyio
async def test_proxy_forwards_to_inventory_service(client):
    token = create_token("u1", "test@example.com")
    mock_resp = httpx.Response(200, json={"items": []})
    with patch(
        "app.service_proxy._forward_request",
        new_callable=AsyncMock,
        return_value=mock_resp,
    ):
        resp = await client.get(
            "/inventory",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200


# ---- Circuit Breaker ----


@pytest.mark.anyio
async def test_circuit_breaker_status(client):
    resp = await client.get("/gateway/circuits")
    assert resp.status_code == 200
    data = resp.json()
    assert "products" in data
    assert "orders" in data
    assert "inventory" in data
    assert data["products"]["state"] == "closed"


@pytest.mark.anyio
async def test_service_unavailable_returns_503(client):
    """When downstream service is unreachable, return 503."""
    with patch(
        "app.service_proxy._forward_request",
        new_callable=AsyncMock,
        side_effect=httpx.ConnectError("Connection refused"),
    ):
        resp = await client.get("/products")
        assert resp.status_code == 503


# ---- Correlation ID ----


@pytest.mark.anyio
async def test_correlation_id_generated(client):
    resp = await client.get("/health")
    assert "x-correlation-id" in resp.headers


@pytest.mark.anyio
async def test_correlation_id_passthrough(client):
    cid = "my-custom-correlation-id"
    resp = await client.get("/health", headers={"X-Correlation-ID": cid})
    assert resp.headers["x-correlation-id"] == cid
