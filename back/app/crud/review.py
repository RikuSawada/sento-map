from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.review import Review
from app.schemas.review import ReviewCreate


async def get_reviews_by_sento(
    db: AsyncSession, sento_id: int, skip: int = 0, limit: int = 50
) -> list[Review]:
    result = await db.execute(
        select(Review)
        .where(Review.sento_id == sento_id)
        .options(selectinload(Review.user))
        .order_by(Review.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


async def create_review(
    db: AsyncSession, user_id: int, sento_id: int, data: ReviewCreate
) -> Review:
    review = Review(
        sento_id=sento_id,
        user_id=user_id,
        rating=data.rating,
        comment=data.comment,
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    # user をロード
    result = await db.execute(
        select(Review)
        .where(Review.id == review.id)
        .options(selectinload(Review.user))
    )
    return result.scalar_one()


async def get_review(db: AsyncSession, review_id: int) -> Review | None:
    result = await db.execute(select(Review).where(Review.id == review_id))
    return result.scalar_one_or_none()
