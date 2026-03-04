from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=1000)


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sento_id: int
    user_id: int
    username: str  # Review.user.username を返す（computed field）
    rating: int
    comment: Optional[str] = None
    created_at: datetime
