from datetime import datetime, timezone

from sqlalchemy import String, Integer, Column, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.db import Base

class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(1000))

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    providers = relationship("Provider", back_populates="service")
    bookings = relationship("Booking", back_populates="service")