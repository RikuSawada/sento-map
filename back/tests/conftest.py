import os

# テスト用環境変数を最初に設定（app インポート前）
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db
from app.models.base import Base

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def test_db():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncTestSession = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with AsyncTestSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    yield AsyncTestSession

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def client(test_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def test_user(test_db):
    from app.schemas.user import UserCreate
    from app.crud import user as crud_user

    async with test_db() as db:
        user = await crud_user.create_user(
            db,
            UserCreate(
                username="testuser",
                email="test@example.com",
                password="password123",
            ),
        )
        return user


@pytest_asyncio.fixture
async def test_sento(test_db):
    from app.models.sento import Sento

    async with test_db() as db:
        sento = Sento(
            name="テスト銭湯",
            address="東京都渋谷区1-1-1",
            lat=35.6762,
            lng=139.6503,
        )
        db.add(sento)
        await db.commit()
        await db.refresh(sento)
        return sento


@pytest.fixture
def auth_token(test_user):
    from app.auth import create_access_token

    return create_access_token({"sub": str(test_user.id)})
