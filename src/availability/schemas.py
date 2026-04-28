from typing import Annotated

from pydantic import BaseModel, Field
from datetime import date, time, datetime

from pydantic.v1 import ConstrainedInt


class AvailabilityRead(BaseModel):
    id: int

    user_id: int
    start_at: datetime
    end_at: datetime
    is_booked: bool

    created_at: datetime
    updated_at: datetime


class AvailabilityCreate(BaseModel):
    provider_id: int
    start_at: datetime
    end_at: datetime


class AvailabilityUpdate(BaseModel):
    is_booked: bool
    start_at: datetime
    end_at: datetime