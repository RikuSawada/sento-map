from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.crud import review as crud_review
from app.crud import sento as crud_sento
from app.database import get_db
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewResponse

router = APIRouter()


@router.get("/{sento_id}/reviews", response_model=list[ReviewResponse])
async def list_reviews(
    sento_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> list[ReviewResponse]:
    skip = (page - 1) * per_page
    reviews = await crud_review.get_reviews_by_sento(db, sento_id, skip=skip, limit=per_page)
    return [
        ReviewResponse(
            id=r.id,
            sento_id=r.sento_id,
            user_id=r.user_id,
            username=r.user.username,
            rating=r.rating,
            comment=r.comment,
            created_at=r.created_at,
        )
        for r in reviews
    ]


@router.post("/{sento_id}/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    sento_id: int,
    data: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReviewResponse:
    sento = await crud_sento.get_sento(db, sento_id)
    if sento is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="銭湯が見つかりません",
        )
    review = await crud_review.create_review(db, user_id=current_user.id, sento_id=sento_id, data=data)
    return ReviewResponse(
        id=review.id,
        sento_id=review.sento_id,
        user_id=review.user_id,
        username=review.user.username,
        rating=review.rating,
        comment=review.comment,
        created_at=review.created_at,
    )
