"""Tests for user-service authentication endpoints."""

# ---- Registration ----


def test_register_success(client):
    resp = client.post(
        "/auth/register",
        json={
            "email": "alice@example.com",
            "password": "password123",
            "name": "Alice",
        },
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "alice@example.com"
    assert data["user"]["name"] == "Alice"
    assert data["user"]["role"] == "customer"
    assert "password" not in data["user"]
    assert "password_hash" not in data["user"]


def test_register_duplicate_email(client, registered_user):
    resp = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "anotherpass1",
            "name": "Duplicate",
        },
    )
    assert resp.status_code == 409
    assert "already exists" in resp.get_json()["error"]


def test_register_invalid_email(client):
    resp = client.post(
        "/auth/register",
        json={"email": "not-an-email", "password": "password123", "name": "Bad"},
    )
    assert resp.status_code == 400
    assert "email" in resp.get_json()["error"].lower()


def test_register_short_password(client):
    resp = client.post(
        "/auth/register",
        json={"email": "new@example.com", "password": "short", "name": "Short"},
    )
    assert resp.status_code == 400
    assert "8 characters" in resp.get_json()["error"]


def test_register_missing_name(client):
    resp = client.post(
        "/auth/register",
        json={"email": "new@example.com", "password": "password123"},
    )
    assert resp.status_code == 400
    assert "name" in resp.get_json()["error"].lower()


def test_register_missing_body(client):
    resp = client.post(
        "/auth/register",
        content_type="application/json",
    )
    assert resp.status_code == 400


def test_register_email_case_insensitive(client):
    client.post(
        "/auth/register",
        json={
            "email": "UPPER@example.com",
            "password": "password123",
            "name": "Upper",
        },
    )
    resp = client.post(
        "/auth/register",
        json={
            "email": "upper@example.com",
            "password": "password123",
            "name": "Lower",
        },
    )
    assert resp.status_code == 409


# ---- Login ----


def test_login_success(client, registered_user):
    data, password = registered_user
    resp = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": password},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert "access_token" in body
    assert body["user"]["email"] == "test@example.com"


def test_login_wrong_password(client, registered_user):
    resp = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "wrongpassword"},
    )
    assert resp.status_code == 401
    assert "invalid" in resp.get_json()["error"].lower()


def test_login_nonexistent_user(client):
    resp = client.post(
        "/auth/login",
        json={"email": "nobody@example.com", "password": "password123"},
    )
    assert resp.status_code == 401


def test_login_missing_fields(client):
    resp = client.post("/auth/login", json={"email": "a@b.com"})
    assert resp.status_code == 400

    resp = client.post("/auth/login", json={"password": "pass"})
    assert resp.status_code == 400


def test_login_email_case_insensitive(client, registered_user):
    _, password = registered_user
    resp = client.post(
        "/auth/login",
        json={"email": "TEST@EXAMPLE.COM", "password": password},
    )
    assert resp.status_code == 200


# ---- /auth/me ----


def test_me_with_valid_token(client, registered_user):
    data, _ = registered_user
    token = data["access_token"]
    resp = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["email"] == "test@example.com"
    assert body["name"] == "Test User"


def test_me_without_token(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_me_with_invalid_token(client):
    resp = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer not.a.valid.token"},
    )
    assert resp.status_code == 401


# ---- Health ----


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] in ("healthy", "ok")
