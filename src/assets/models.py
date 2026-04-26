from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, String, Boolean, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.db import Base

class ServiceImage(Base):
    __tablename__ = "service_images"
    __table_args__ = (
        UniqueConstraint("imagekit_file_id", name="uq_service_images_imagekit_file_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id", ondelete="CASCADE"), index=True, nullable=False)

    imagekit_file_id: Mapped[str] = mapped_column(String(255), nullable=False)   # ImageKit fileId
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    thumbnail_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)     # e.g. /services/cleaning/...
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    size: Mapped[int | None] = mapped_column(nullable=True)

    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                                                 onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    service = relationship("Service", back_populates="images")