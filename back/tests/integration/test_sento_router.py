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


async def test_list_sentos_empty(client):
    resp = await client.get("/sentos")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["per_page"] == 50


async def test_list_sentos_with_data(client, test_db):
    await _seed_sento(test_db, name="銭湯A")
    await _seed_sento(test_db, name="銭湯B", lat=35.7, lng=139.7)
    resp = await client.get("/sentos")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


async def test_list_sentos_pagination(client, test_db):
    for i in range(5):
        await _seed_sento(test_db, name=f"銭湯{i}", lat=35.0 + i * 0.01, lng=139.0 + i * 0.01)
    resp = await client.get("/sentos?page=1&per_page=2")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["per_page"] == 2


async def test_list_sentos_page2(client, test_db):
    for i in range(5):
        await _seed_sento(test_db, name=f"銭湯{i}", lat=35.0 + i * 0.01, lng=139.0 + i * 0.01)
    resp = await client.get("/sentos?page=2&per_page=2")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["page"] == 2


async def test_list_sentos_with_bounds_filter(client, test_db):
    await _seed_sento(test_db, name="範囲内銭湯", lat=35.6762, lng=139.6503)
    await _seed_sento(test_db, name="範囲外銭湯", lat=36.0, lng=139.6503)
    resp = await client.get("/sentos?lat_min=35.0&lat_max=35.8&lng_min=139.0&lng_max=140.0")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "範囲内銭湯"


async def test_list_sentos_invalid_page(client):
    resp = await client.get("/sentos?page=0")
    assert resp.status_code == 422


async def test_list_sentos_per_page_too_large(client):
    resp = await client.get("/sentos?per_page=501")
    assert resp.status_code == 422


async def test_get_sento_success(client, test_db):
    sento = await _seed_sento(test_db, name="詳細銭湯", phone="03-1234-5678")
    resp = await client.get(f"/sentos/{sento.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == sento.id
    assert data["name"] == "詳細銭湯"
    assert data["address"] == "東京都渋谷区1-1-1"
    assert data["lat"] == 35.6762
    assert data["lng"] == 139.6503
    assert data["phone"] == "03-1234-5678"
    assert "created_at" in data
    assert "updated_at" in data


async def test_get_sento_not_found(client):
    resp = await client.get("/sentos/99999")
    assert resp.status_code == 404
    assert "銭湯" in resp.json()["detail"]


async def test_get_sento_optional_fields_null(client, test_db):
    sento = await _seed_sento(test_db)
    resp = await client.get(f"/sentos/{sento.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["phone"] is None
    assert data["url"] is None
    assert data["open_hours"] is None
    assert data["holiday"] is None
