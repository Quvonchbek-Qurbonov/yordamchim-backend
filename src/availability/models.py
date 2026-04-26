from __future__ import annotations

from datetime import datetime, timezone, time, date
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Date, Time, Boolean, DateTime, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.db import Base


if TYPE_CHECKING:
    from src.users import User
    from src.bookings import Booking


class Availability(Base):
    __tablename__ = "availability"
    __table_args__ = (
        CheckConstraint("end_time > start_time", name="ck_availability_time_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)

    is_booked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    provider: Mapped["User"] = relationship("User", back_populates="availability")
    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="availability")