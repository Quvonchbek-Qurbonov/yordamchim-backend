from __future__ import annotations
from typing import TYPE_CHECKING

from sqlalchemy import (
    String, DateTime, ForeignKey, Enum as SAEnum, Index, Numeric, CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from decimal import Decimal
from datetime import datetime, timezone
from src.core.db import Base
from enum import Enum


if TYPE_CHECKING:
    from src.users import User
    from src.services import Service
    from src.availability import Availability


class BookingStatus(Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"



class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        CheckConstraint("end_at > start_at", name="ck_booking_time_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id", ondelete="RESTRICT"), nullable=False, index=True)

    availability_id: Mapped[int | None] = mapped_column(
        ForeignKey("availability.id", ondelete="SET NULL"), nullable=True
    )

    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    status: Mapped[BookingStatus] = mapped_column(
        SAEnum(BookingStatus, name="booking_status"),
        default=BookingStatus.pending,
        nullable=False,
        index=True,
    )

    total_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="bookings")
    provider: Mapped["User"] = relationship("User", foreign_keys=[provider_id], back_populates="provided_bookings")
    service: Mapped["Service"] = relationship("Service", back_populates="bookings")
    availability: Mapped["Availability | None"] = relationship("Availability", back_populates="bookings")