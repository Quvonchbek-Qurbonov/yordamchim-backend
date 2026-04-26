from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, Column, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.db import Base


if TYPE_CHECKING:
    from src.bookings import Booking
    from src.providers import ProviderService

class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    provider_links: Mapped[list["ProviderService"]] = relationship(
        "ProviderService",
        back_populates="service",
        cascade="all, delete-orphan",
    )

    bookings: Mapped[list["Booking"]] = relationship(
        "Booking",
        back_populates="service",
    )

    images = relationship("ServiceImage", back_populates="service", cascade="all, delete-orphan")

