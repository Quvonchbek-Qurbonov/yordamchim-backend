from sqlalchemy import Integer, ForeignKey, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from src.core.db import Base
from enum import Enum


class BookingStatus(Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"



class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    provider_id: Mapped[int] = mapped_column(ForeignKey("providers.id"))
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"))

    booking_time: Mapped[datetime] = mapped_column()
    status: Mapped[BookingStatus] = mapped_column(default=BookingStatus.pending)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # relationships
    user = relationship("User", back_populates="bookings")
    provider = relationship("Provider", back_populates="bookings")
    service = relationship("Service", back_populates="bookings")