from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String, Boolean, DateTime, Enum as SAEnum
from datetime import datetime, timezone
from sqlalchemy.orm import relationship, mapped_column, Mapped
from enum import Enum

from src.core.db import Base


if TYPE_CHECKING:
    from src.bookings import Booking
    from src.availability import Availability
    from src.providers import Profile, ProviderService


class Roles(Enum):
    admin = "admin"
    user = "user"
    provider = "provider"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    google_sub: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    password: Mapped[str | None] = mapped_column(String(255), nullable=True)  # nullable for Google auth users
    role: Mapped[Roles] = mapped_column(SAEnum(Roles, name="user_roles"), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    # bookings as customer
    bookings: Mapped[list["Booking"]] = relationship(
        "Booking",
        foreign_keys="Booking.user_id",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # bookings as provider
    provided_bookings: Mapped[list["Booking"]] = relationship(
        "Booking",
        foreign_keys="Booking.provider_id",
        back_populates="provider",
    )

    availability: Mapped[list["Availability"]] = relationship(
        "Availability",
        back_populates="provider",
        cascade="all, delete-orphan",
    )

    profile: Mapped["Profile | None"] = relationship(
        "Profile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    provider_services: Mapped[list["ProviderService"]] = relationship(
        "ProviderService",
        back_populates="user",
        cascade="all, delete-orphan",
    )