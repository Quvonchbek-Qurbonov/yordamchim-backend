from sqlalchemy import Integer, ForeignKey, Date, Time, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.db import Base

class Availability(Base):
    __tablename__ = "availability"

    id: Mapped[int] = mapped_column(primary_key=True)

    provider_id: Mapped[int] = mapped_column(ForeignKey("providers.id"))

    date: Mapped[str] = mapped_column(Date)
    start_time: Mapped[str] = mapped_column(Time)
    end_time: Mapped[str] = mapped_column(Time)

    is_booked: Mapped[bool] = mapped_column(default=False)

    provider = relationship("Provider", back_populates="availability")