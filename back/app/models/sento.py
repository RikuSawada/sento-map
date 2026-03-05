from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.review import Review


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Sento(Base):
    __tablename__ = "sentos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    address: Mapped[str] = mapped_column(String, nullable=False)
    lat: Mapped[Optional[float]] = mapped_column(nullable=True)
    lng: Mapped[Optional[float]] = mapped_column(nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    open_hours: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    holiday: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    prefecture: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, index=True)
    region: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    geocoded_by: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    facility_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    reviews: Mapped[List["Review"]] = relationship(
        "Review", back_populates="sento", cascade="all, delete-orphan"
    )
