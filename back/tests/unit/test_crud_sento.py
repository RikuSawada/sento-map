import pytest

from app.models.sento import Sento
from app.crud import sento as crud_sento


async def _create_sento(db, **kwargs) -> Sento:
    defaults = dict(
        name="テスト銭湯",
        address="東京都渋谷区1-1-1",
        lat=35.6762,
        lng=139.6503,
    )
    defaults.update(kwargs)
    s = Sento(**defaults)
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return s


async def test_get_sento_found(test_db, test_sento):
    async with test_db() as db:
        found = await crud_sento.get_sento(db, test_sento.id)
        assert found is not None
        assert found.name == "テスト銭湯"
        assert found.address == "東京都渋谷区1-1-1"


async def test_get_sento_not_found(test_db):
    async with test_db() as db:
        found = await crud_sento.get_sento(db, 99999)
        assert found is None


async def test_get_sentos_empty(test_db):
    async with test_db() as db:
        items, total = await crud_sento.get_sentos(db)
        assert items == []
        assert total == 0


async def test_get_sentos_with_data(test_db, test_sento):
    async with test_db() as db:
        items, total = await crud_sento.get_sentos(db)
        assert total == 1
        assert items[0].name == "テスト銭湯"


async def test_get_sentos_with_lat_bounds_inside(test_db, test_sento):
    async with test_db() as db:
        items, total = await crud_sento.get_sentos(
            db, lat_min=35.0, lat_max=36.0, lng_min=139.0, lng_max=140.0
        )
        assert total == 1
        assert items[0].name == "テスト銭湯"


async def test_get_sentos_with_lat_bounds_outside(test_db, test_sento):
    async with test_db() as db:
        items, total = await crud_sento.get_sentos(
            db, lat_min=36.0, lat_max=37.0
        )
        assert total == 0
        assert items == []


async def test_get_sentos_with_lng_bounds_outside(test_db, test_sento):
    async with test_db() as db:
        items, total = await crud_sento.get_sentos(
            db, lng_min=140.0, lng_max=141.0
        )
        assert total == 0


async def test_get_sentos_skip_limit(test_db):
    async with test_db() as db:
        s1 = await _create_sento(db, name="銭湯A", address="A", lat=35.0, lng=139.0)
        s2 = await _create_sento(db, name="銭湯B", address="B", lat=35.1, lng=139.1)
        s3 = await _create_sento(db, name="銭湯C", address="C", lat=35.2, lng=139.2)

    async with test_db() as db:
        items, total = await crud_sento.get_sentos(db, skip=0, limit=2)
        assert total == 3
        assert len(items) == 2


async def test_upsert_sento_create_new(test_db):
    async with test_db() as db:
        sento = await crud_sento.upsert_sento(
            db,
            {
                "name": "新銭湯",
                "address": "東京都台東区1-1",
                "lat": 35.7,
                "lng": 139.7,
                "url": "http://example.com/sento1",
            },
        )
        assert sento.id is not None
        assert sento.name == "新銭湯"
        assert sento.url == "http://example.com/sento1"


async def test_upsert_sento_update_existing(test_db):
    async with test_db() as db:
        s1 = await crud_sento.upsert_sento(
            db,
            {
                "name": "旧名前",
                "address": "旧住所",
                "lat": 35.7,
                "lng": 139.7,
                "url": "http://example.com/sento-upsert",
            },
        )
        original_id = s1.id

    async with test_db() as db:
        s2 = await crud_sento.upsert_sento(
            db,
            {
                "name": "新名前",
                "address": "新住所",
                "lat": 35.8,
                "lng": 139.8,
                "url": "http://example.com/sento-upsert",
            },
        )
        assert s2.id == original_id
        assert s2.name == "新名前"
        assert s2.address == "新住所"


async def test_get_sentos_with_prefecture_filter(test_db):
    async with test_db() as db:
        s_tokyo = Sento(name="東京銭湯", address="東京都渋谷区1-1", lat=35.6, lng=139.6, prefecture="東京都")
        s_osaka = Sento(name="大阪銭湯", address="大阪府大阪市1-1", lat=34.6, lng=135.5, prefecture="大阪府")
        db.add_all([s_tokyo, s_osaka])
        await db.commit()

    async with test_db() as db:
        items, total = await crud_sento.get_sentos(db, prefecture="東京都")
        assert total == 1
        assert items[0].name == "東京銭湯"

    async with test_db() as db:
        items, total = await crud_sento.get_sentos(db, prefecture="大阪府")
        assert total == 1
        assert items[0].name == "大阪銭湯"


async def test_upsert_sento_no_url_creates_new(test_db):
    async with test_db() as db:
        s1 = await crud_sento.upsert_sento(
            db,
            {
                "name": "URLなし銭湯",
                "address": "住所1",
                "lat": 35.5,
                "lng": 139.5,
            },
        )
        s2 = await crud_sento.upsert_sento(
            db,
            {
                "name": "URLなし銭湯2",
                "address": "住所2",
                "lat": 35.6,
                "lng": 139.6,
            },
        )
        assert s1.id != s2.id


async def test_upsert_sento_source_url_match(test_db):
    """source_url が一致すれば UPDATE される。"""
    async with test_db() as db:
        s1 = await crud_sento.upsert_sento(
            db,
            {
                "name": "旧名前",
                "address": "旧住所",
                "lat": 35.5,
                "lng": 139.5,
                "source_url": "https://www.1010.or.jp/map/item/item-cnt-1/",
            },
        )
        original_id = s1.id

    async with test_db() as db:
        s2 = await crud_sento.upsert_sento(
            db,
            {
                "name": "新名前",
                "address": "新住所",
                "lat": 35.6,
                "lng": 139.6,
                "source_url": "https://www.1010.or.jp/map/item/item-cnt-1/",
            },
        )
        assert s2.id == original_id
        assert s2.name == "新名前"
        assert s2.address == "新住所"


async def test_upsert_sento_source_url_takes_priority_over_url(test_db):
    """source_url が url より優先されて UPDATE される。"""
    async with test_db() as db:
        s1 = await crud_sento.upsert_sento(
            db,
            {
                "name": "元の銭湯",
                "address": "元の住所",
                "lat": 35.5,
                "lng": 139.5,
                "url": "http://official.example.com/",
                "source_url": "https://www.1010.or.jp/map/item/item-cnt-2/",
            },
        )
        original_id = s1.id

    async with test_db() as db:
        # source_url は同じ、url は変わっている（スクレイピング再実行想定）
        s2 = await crud_sento.upsert_sento(
            db,
            {
                "name": "更新された銭湯",
                "address": "更新された住所",
                "lat": 35.6,
                "lng": 139.6,
                "url": "http://official.example.com/",
                "source_url": "https://www.1010.or.jp/map/item/item-cnt-2/",
            },
        )
        assert s2.id == original_id
        assert s2.name == "更新された銭湯"


async def test_upsert_sento_same_name_different_prefecture(test_db):
    """同名・同住所でも都道府県が異なれば別レコードとして INSERT される。"""
    async with test_db() as db:
        s_tokyo = await crud_sento.upsert_sento(
            db,
            {
                "name": "梅の湯",
                "address": "中央区1-1-1",
                "lat": 35.6,
                "lng": 139.6,
                "prefecture": "東京都",
            },
        )
        s_osaka = await crud_sento.upsert_sento(
            db,
            {
                "name": "梅の湯",
                "address": "中央区1-1-1",
                "lat": 34.6,
                "lng": 135.5,
                "prefecture": "大阪府",
            },
        )
        assert s_tokyo.id != s_osaka.id


async def test_upsert_sento_name_address_prefecture_updates(test_db):
    """source_url・url がなく name+address+prefecture が一致すれば UPDATE される。"""
    async with test_db() as db:
        s1 = await crud_sento.upsert_sento(
            db,
            {
                "name": "富士の湯",
                "address": "新宿区1-1-1",
                "lat": 35.5,
                "lng": 139.5,
                "prefecture": "東京都",
            },
        )
        original_id = s1.id

    async with test_db() as db:
        s2 = await crud_sento.upsert_sento(
            db,
            {
                "name": "富士の湯",
                "address": "新宿区1-1-1",
                "lat": 35.55,
                "lng": 139.55,
                "prefecture": "東京都",
            },
        )
        assert s2.id == original_id
        assert s2.lat == 35.55


async def test_upsert_sento_facility_type_persisted(test_db):
    """facility_type が正しく保存・取得される。"""
    async with test_db() as db:
        s = await crud_sento.upsert_sento(
            db,
            {
                "name": "温泉銭湯",
                "address": "東京都江東区1-1",
                "lat": 35.6,
                "lng": 139.8,
                "facility_type": "onsen",
            },
        )
        assert s.facility_type == "onsen"


async def test_upsert_sento_facility_type_update(test_db):
    """upsert で facility_type が更新される。"""
    async with test_db() as db:
        s1 = await crud_sento.upsert_sento(
            db,
            {
                "name": "スパ銭湯",
                "address": "大阪府大阪市1-1",
                "lat": 34.6,
                "lng": 135.5,
                "url": "https://example.com/spa",
                "facility_type": "sento",
            },
        )
        original_id = s1.id

    async with test_db() as db:
        s2 = await crud_sento.upsert_sento(
            db,
            {
                "name": "スパ銭湯",
                "address": "大阪府大阪市1-1",
                "lat": 34.6,
                "lng": 135.5,
                "url": "https://example.com/spa",
                "facility_type": "super_sento",
            },
        )
        assert s2.id == original_id
        assert s2.facility_type == "super_sento"
