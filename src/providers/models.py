from __future__ import annotations
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.db import Base


if TYPE_CHECKING:
    from src.users import User
    from src.services import Service


class Profile(Base):
    __tablename__ = "profiles"
    __table_args__ = (UniqueConstraint("user_id", name="uq_profiles_user_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    bio: Mapped[str | None] = mapped_column(String(500), nullable=True)
    about: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    experience_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rating_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    rating_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    user: Mapped["User"] = relationship("User", back_populates="profile")


class ProviderService(Base):
    __tablename__ = "provider_services"
    __table_args__ = (
        UniqueConstraint("user_id", "service_id", name="uq_provider_service"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id", ondelete="CASCADE"), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="provider_services")
    service: Mapped["Service"] = relationship("Service", back_populates="provider_links")