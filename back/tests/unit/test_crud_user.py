import bcrypt
import pytest

from app.schemas.user import UserCreate
from app.crud import user as crud_user


async def test_create_user_password_hashed(test_db):
    async with test_db() as db:
        user = await crud_user.create_user(
            db,
            UserCreate(
                username="hashtest",
                email="hash@test.com",
                password="plainpassword",
            ),
        )
        assert user.hashed_password != "plainpassword"
        assert bcrypt.checkpw(b"plainpassword", user.hashed_password.encode())


async def test_create_user_fields_stored(test_db):
    async with test_db() as db:
        user = await crud_user.create_user(
            db,
            UserCreate(
                username="fieldstest",
                email="fields@test.com",
                password="password123",
            ),
        )
        assert user.username == "fieldstest"
        assert user.email == "fields@test.com"
        assert user.id is not None
        assert user.created_at is not None


async def test_get_user_by_email_found(test_db, test_user):
    async with test_db() as db:
        found = await crud_user.get_user_by_email(db, "test@example.com")
        assert found is not None
        assert found.username == "testuser"
        assert found.email == "test@example.com"


async def test_get_user_by_email_not_found(test_db):
    async with test_db() as db:
        found = await crud_user.get_user_by_email(db, "nonexistent@example.com")
        assert found is None


async def test_get_user_by_id_found(test_db, test_user):
    async with test_db() as db:
        found = await crud_user.get_user(db, test_user.id)
        assert found is not None
        assert found.email == "test@example.com"


async def test_get_user_not_found(test_db):
    async with test_db() as db:
        found = await crud_user.get_user(db, 99999)
        assert found is None


async def test_create_multiple_users(test_db):
    async with test_db() as db:
        u1 = await crud_user.create_user(
            db,
            UserCreate(username="user1", email="u1@test.com", password="password123"),
        )
        u2 = await crud_user.create_user(
            db,
            UserCreate(username="user2", email="u2@test.com", password="password123"),
        )
        assert u1.id != u2.id
