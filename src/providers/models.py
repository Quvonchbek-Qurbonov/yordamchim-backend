from sqlalchemy import String, Integer, Float, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.db import Base

class Provider(Base):
    __tablename__ = "providers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    phone: Mapped[str] = mapped_column(String)

    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"))

    rating: Mapped[float] = mapped_column(default=0.0)
    is_active: Mapped[bool] = mapped_column(default=True)

    # relationships
    service = relationship("Service", back_populates="providers")
    availability = relationship("Availability", back_populates="provider")
    bookings = relationship("Booking", back_populates="provider")