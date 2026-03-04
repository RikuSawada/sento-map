from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import sento as crud_sento
from app.database import get_db
from app.schemas.sento import SentoListResponse, SentoResponse

router = APIRouter()


@router.get("", response_model=SentoListResponse)
async def list_sentos(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=500),
    lat_min: Optional[float] = Query(None),
    lat_max: Optional[float] = Query(None),
    lng_min: Optional[float] = Query(None),
    lng_max: Optional[float] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> SentoListResponse:
    skip = (page - 1) * per_page
    items, total = await crud_sento.get_sentos(
        db,
        skip=skip,
        limit=per_page,
        lat_min=lat_min,
        lat_max=lat_max,
        lng_min=lng_min,
        lng_max=lng_max,
    )
    return SentoListResponse(
        items=[SentoResponse.model_validate(s) for s in items],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{sento_id}", response_model=SentoResponse)
async def get_sento(
    sento_id: int,
    db: AsyncSession = Depends(get_db),
) -> SentoResponse:
    sento = await crud_sento.get_sento(db, sento_id)
    if sento is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="銭湯が見つかりません",
        )
    return SentoResponse.model_validate(sento)
