from datetime import datetime
from decimal import Decimal
from typing import Optional, Annotated

from pydantic import BaseModel, Field, StringConstraints, ConfigDict

from src.bookings.models import BookingStatus
from src.users.schemas import UserRead
from src.providers.schemas import ProviderRead
from src.services.schemas import ServiceRead
from src.availability.schemas import AvailabilityRead


class BookingCreate(BaseModel):
    user_id: Annotated[int, Field(gt=0)]
    provider_id: Annotated[int, Field(gt=0)]
    service_id: Annotated[int, Field(gt=0)]
    availability_id: Annotated[int, Field(gt=0)]

    start_at: datetime
    end_at: datetime

    # usually set by backend; keep optional if you want to allow client value
    status: BookingStatus = BookingStatus.pending

    total_price: Annotated[Decimal, Field(ge=0, max_digits=10, decimal_places=2)]
    notes: Optional[Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]] = None


class BookingRead(BaseModel):
    id: int

    user: UserRead
    provider: ProviderRead
    service: ServiceRead
    availability: AvailabilityRead

    start_at: datetime
    end_at: datetime
    status: BookingStatus
    total_price: Annotated[Decimal, Field(ge=0, max_digits=10, decimal_places=2)]
    notes: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BookingUpdate(BaseModel):
    # If only these statuses are allowed by your flow, enforce in service logic too
    status: Optional[BookingStatus] = None
    notes: Optional[Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]] = None