from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session, joinedload
from typing import List

from src.availability import Availability
from src.bookings import Booking
from src.core.db import get_db
from src.providers.schemas import ProviderUpdate, ProviderRead, ProviderCreate
from src.services import Service

router = APIRouter(prefix="/providers", tags=["Providers"])

