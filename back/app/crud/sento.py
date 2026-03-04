from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sento import Sento


async def get_sento(db: AsyncSession, sento_id: int) -> Sento | None:
    result = await db.execute(select(Sento).where(Sento.id == sento_id))
    return result.scalar_one_or_none()


async def get_sentos(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    lat_min: Optional[float] = None,
    lat_max: Optional[float] = None,
    lng_min: Optional[float] = None,
    lng_max: Optional[float] = None,
) -> tuple[list[Sento], int]:
    stmt = select(Sento)
    if lat_min is not None:
        stmt = stmt.where(Sento.lat >= lat_min)
    if lat_max is not None:
        stmt = stmt.where(Sento.lat <= lat_max)
    if lng_min is not None:
        stmt = stmt.where(Sento.lng >= lng_min)
    if lng_max is not None:
        stmt = stmt.where(Sento.lng <= lng_max)
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()
    result = await db.execute(stmt.offset(skip).limit(limit))
    return result.scalars().all(), total


async def upsert_sento(db: AsyncSession, data: dict) -> Sento:
    """バッチからの差分更新。url でユニーク判定。"""
    existing = None
    if data.get("url"):
        result = await db.execute(select(Sento).where(Sento.url == data["url"]))
        existing = result.scalar_one_or_none()
    if existing:
        for key, value in data.items():
            setattr(existing, key, value)
        await db.commit()
        await db.refresh(existing)
        return existing
    else:
        sento = Sento(**data)
        db.add(sento)
        await db.commit()
        await db.refresh(sento)
        return sento
