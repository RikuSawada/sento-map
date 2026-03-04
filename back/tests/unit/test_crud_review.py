import pytest

from app.models.sento import Sento
from app.models.user import User
from app.schemas.review import ReviewCreate
from app.crud import review as crud_review


async def _seed_user_and_sento(db) -> tuple[User, Sento]:
    import bcrypt

    hashed = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode()
    user = User(username="reviewer", email="reviewer@test.com", hashed_password=hashed)
    db.add(user)

    sento = Sento(name="テスト銭湯", address="東京都1-1", lat=35.6, lng=139.6)
    db.add(sento)
    await db.commit()
    await db.refresh(user)
    await db.refresh(sento)
    return user, sento


async def test_create_review_basic(test_db):
    async with test_db() as db:
        user, sento = await _seed_user_and_sento(db)
        review = await crud_review.create_review(
            db,
            user_id=user.id,
            sento_id=sento.id,
            data=ReviewCreate(rating=4, comment="良い銭湯"),
        )
        assert review.id is not None
        assert review.rating == 4
        assert review.comment == "良い銭湯"
        assert review.user_id == user.id
        assert review.sento_id == sento.id
        assert review.user.username == "reviewer"


async def test_create_review_without_comment(test_db):
    async with test_db() as db:
        user, sento = await _seed_user_and_sento(db)
        review = await crud_review.create_review(
            db,
            user_id=user.id,
            sento_id=sento.id,
            data=ReviewCreate(rating=5),
        )
        assert review.comment is None
        assert review.rating == 5


async def test_get_reviews_by_sento_empty(test_db):
    async with test_db() as db:
        sento = Sento(name="銭湯", address="住所", lat=35.6, lng=139.6)
        db.add(sento)
        await db.commit()
        await db.refresh(sento)

        reviews = await crud_review.get_reviews_by_sento(db, sento.id)
        assert reviews == []


async def test_get_reviews_by_sento_with_data(test_db):
    async with test_db() as db:
        user, sento = await _seed_user_and_sento(db)
        await crud_review.create_review(
            db, user_id=user.id, sento_id=sento.id, data=ReviewCreate(rating=3, comment="普通")
        )
        await crud_review.create_review(
            db, user_id=user.id, sento_id=sento.id, data=ReviewCreate(rating=5, comment="最高")
        )
        reviews = await crud_review.get_reviews_by_sento(db, sento.id)
        assert len(reviews) == 2
        # created_at.desc() でソートされているので最新が先頭
        assert reviews[0].rating == 5


async def test_get_reviews_by_sento_skip_limit(test_db):
    async with test_db() as db:
        user, sento = await _seed_user_and_sento(db)
        for i in range(5):
            await crud_review.create_review(
                db, user_id=user.id, sento_id=sento.id, data=ReviewCreate(rating=3)
            )
        reviews = await crud_review.get_reviews_by_sento(db, sento.id, skip=0, limit=3)
        assert len(reviews) == 3


async def test_get_review_found(test_db):
    async with test_db() as db:
        user, sento = await _seed_user_and_sento(db)
        created = await crud_review.create_review(
            db, user_id=user.id, sento_id=sento.id, data=ReviewCreate(rating=2)
        )
        found = await crud_review.get_review(db, created.id)
        assert found is not None
        assert found.id == created.id


async def test_get_review_not_found(test_db):
    async with test_db() as db:
        found = await crud_review.get_review(db, 99999)
        assert found is None


async def test_get_reviews_by_different_sento_isolated(test_db):
    async with test_db() as db:
        import bcrypt

        hashed = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode()
        user = User(username="user_iso", email="iso@test.com", hashed_password=hashed)
        db.add(user)
        sento_a = Sento(name="銭湯A", address="A", lat=35.0, lng=139.0)
        sento_b = Sento(name="銭湯B", address="B", lat=35.1, lng=139.1)
        db.add(sento_a)
        db.add(sento_b)
        await db.commit()
        await db.refresh(user)
        await db.refresh(sento_a)
        await db.refresh(sento_b)

        await crud_review.create_review(
            db, user_id=user.id, sento_id=sento_a.id, data=ReviewCreate(rating=5)
        )
        reviews_b = await crud_review.get_reviews_by_sento(db, sento_b.id)
        assert reviews_b == []
