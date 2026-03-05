from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class SentoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    address: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    phone: Optional[str] = None
    url: Optional[str] = None
    open_hours: Optional[str] = None
    holiday: Optional[str] = None
    prefecture: Optional[str] = None
    region: Optional[str] = None
    source_url: Optional[str] = None
    geocoded_by: Optional[str] = None
    facility_type: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class SentoListResponse(BaseModel):
    items: list[SentoResponse]
    total: int
    page: int
    per_page: int
