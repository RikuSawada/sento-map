import pytest

from app.models.sento import Sento


async def _seed_sento(test_db, **kwargs) -> Sento:
    defaults = dict(
        name="テスト銭湯",
        address="東京都渋谷区1-1-1",
        lat=35.6762,
        lng=139.6503,
    )
    defaults.update(kwargs)
    async with test_db() as db:
        s = Sento(**defaults)
        db.add(s)
        await db.commit()
        await db.refresh(s)
        return s


async def _register_and_login(client, email: str, username: str, password: str = "password123") -> str:
    await client.post(
        "/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    login_resp = await client.post(
        "/auth/login",
        data={"username": email, "password": password},
    )
    return login_resp.json()["access_token"]


async def test_list_reviews_empty(client, test_db):
    sento = await _seed_sento(test_db)
    resp = await client.get(f"/sentos/{sento.id}/reviews")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_reviews_nonexistent_sento(client):
    # 存在しない銭湯のレビュー一覧は空リストを返す（404ではない）
    resp = await client.get("/sentos/99999/reviews")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_create_review_unauthorized(client):
    resp = await client.post("/sentos/1/reviews", json={"rating": 5, "comment": "good"})
    assert resp.status_code == 401


async def test_create_review_sento_not_found(client):
    token = await _register_and_login(client, "rtest@example.com", "rtest")
    resp = await client.post(
        "/sentos/99999/reviews",
        json={"rating": 5, "comment": "good"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404
    assert "銭湯" in resp.json()["detail"]


async def test_create_review_success(client, test_db):
    sento = await _seed_sento(test_db)
    token = await _register_and_login(client, "reviewer@example.com", "reviewer")
    resp = await client.post(
        f"/sentos/{sento.id}/reviews",
        json={"rating": 4, "comment": "良い銭湯でした"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["rating"] == 4
    assert data["comment"] == "良い銭湯でした"
    assert data["sento_id"] == sento.id
    assert "id" in data
    assert "user_id" in data
    assert "username" in data
    assert "created_at" in data
    assert data["username"] == "reviewer"


async def test_create_review_without_comment(client, test_db):
    sento = await _seed_sento(test_db)
    token = await _register_and_login(client, "nocomment@example.com", "nocomment")
    resp = await client.post(
        f"/sentos/{sento.id}/reviews",
        json={"rating": 5},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["rating"] == 5
    assert data["comment"] is None


async def test_create_review_invalid_rating_too_low(client, test_db):
    sento = await _seed_sento(test_db)
    token = await _register_and_login(client, "lowrating@example.com", "lowrating")
    resp = await client.post(
        f"/sentos/{sento.id}/reviews",
        json={"rating": 0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


async def test_create_review_invalid_rating_too_high(client, test_db):
    sento = await _seed_sento(test_db)
    token = await _register_and_login(client, "highrating@example.com", "highrating")
    resp = await client.post(
        f"/sentos/{sento.id}/reviews",
        json={"rating": 6},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


async def test_list_reviews_after_create(client, test_db):
    sento = await _seed_sento(test_db)
    token = await _register_and_login(client, "listtest@example.com", "listtest")
    await client.post(
        f"/sentos/{sento.id}/reviews",
        json={"rating": 3, "comment": "普通"},
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(
        f"/sentos/{sento.id}/reviews",
        json={"rating": 5, "comment": "最高"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.get(f"/sentos/{sento.id}/reviews")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


async def test_create_review_with_invalid_token(client, test_db):
    sento = await _seed_sento(test_db)
    resp = await client.post(
        f"/sentos/{sento.id}/reviews",
        json={"rating": 3},
        headers={"Authorization": "Bearer invalidtoken"},
    )
    assert resp.status_code == 401


async def test_list_reviews_pagination(client, test_db):
    sento = await _seed_sento(test_db)
    token = await _register_and_login(client, "page@example.com", "pageuser")
    for i in range(5):
        await client.post(
            f"/sentos/{sento.id}/reviews",
            json={"rating": 3},
            headers={"Authorization": f"Bearer {token}"},
        )
    resp = await client.get(f"/sentos/{sento.id}/reviews?page=1&per_page=2")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
