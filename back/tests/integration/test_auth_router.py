import pytest


async def test_register_success(client):
    resp = await client.post(
        "/auth/register",
        json={"username": "newuser", "email": "new@example.com", "password": "password123"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "new@example.com"
    assert data["username"] == "newuser"
    assert "id" in data
    assert "created_at" in data
    assert "password" not in data
    assert "hashed_password" not in data


async def test_register_duplicate_email(client):
    payload = {"username": "u1", "email": "dup@example.com", "password": "password123"}
    r1 = await client.post("/auth/register", json=payload)
    assert r1.status_code == 201
    r2 = await client.post(
        "/auth/register",
        json={"username": "u2", "email": "dup@example.com", "password": "password123"},
    )
    assert r2.status_code == 400
    assert "メールアドレス" in r2.json()["detail"]


async def test_register_invalid_email(client):
    resp = await client.post(
        "/auth/register",
        json={"username": "u", "email": "not-an-email", "password": "password123"},
    )
    assert resp.status_code == 422


async def test_register_password_too_short(client):
    resp = await client.post(
        "/auth/register",
        json={"username": "u", "email": "a@b.com", "password": "short"},
    )
    assert resp.status_code == 422


async def test_login_success(client):
    await client.post(
        "/auth/register",
        json={"username": "login_user", "email": "login@example.com", "password": "password123"},
    )
    resp = await client.post(
        "/auth/login",
        data={"username": "login@example.com", "password": "password123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(client):
    await client.post(
        "/auth/register",
        json={"username": "wpwd_user", "email": "wpwd@example.com", "password": "password123"},
    )
    resp = await client.post(
        "/auth/login",
        data={"username": "wpwd@example.com", "password": "wrongpassword"},
    )
    assert resp.status_code == 401
    assert "WWW-Authenticate" in resp.headers


async def test_login_nonexistent_user(client):
    resp = await client.post(
        "/auth/login",
        data={"username": "nobody@example.com", "password": "password123"},
    )
    assert resp.status_code == 401


async def test_me_without_token(client):
    resp = await client.get("/auth/me")
    assert resp.status_code == 401


async def test_me_with_valid_token(client):
    await client.post(
        "/auth/register",
        json={"username": "me_user", "email": "me@example.com", "password": "password123"},
    )
    login_resp = await client.post(
        "/auth/login",
        data={"username": "me@example.com", "password": "password123"},
    )
    token = login_resp.json()["access_token"]
    resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@example.com"


async def test_me_with_invalid_token(client):
    resp = await client.get("/auth/me", headers={"Authorization": "Bearer invalidtoken"})
    assert resp.status_code == 401


async def test_me_with_malformed_authorization(client):
    resp = await client.get("/auth/me", headers={"Authorization": "NotBearer token"})
    assert resp.status_code == 401
