from typing import Annotated

from pydantic import BaseModel, Field
from datetime import date, time, datetime

from pydantic.v1 import ConstrainedInt


class AvailabilityRead(BaseModel):
    id: int

    provider_id: int
    date: date
    start_time: time
    end_time: time
    is_booked: bool

    created_at: datetime
    updated_at: datetime


class AvailabilityCreate(BaseModel):
    provider_id: int
    date: date
    start_time: time
    end_time: time


class AvailabilityUpdate(BaseModel):
    is_booked: bool
    date: date
    start_time: time
    end_time: time