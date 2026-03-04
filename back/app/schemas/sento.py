from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class SentoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    address: str
    lat: float
    lng: float
    phone: Optional[str] = None
    url: Optional[str] = None
    open_hours: Optional[str] = None
    holiday: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class SentoListResponse(BaseModel):
    items: list[SentoResponse]
    total: int
    page: int
    per_page: int
