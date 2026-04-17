from datetime import datetime

from pydantic import BaseModel
from src.services.schemas import ServiceRead


class ProviderRead(BaseModel):
    id : int
    name : str
    phone : str
    service: ServiceRead
    rating : float
    is_active : bool
    created_at : datetime
    updated_at : datetime


class ProviderCreate(BaseModel):
    name : str
    phone : str
    service_id : int


class ProviderUpdate(BaseModel):
    name : str
    service_id : int