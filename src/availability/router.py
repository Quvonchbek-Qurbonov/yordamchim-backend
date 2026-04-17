from typing import Optional, List
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from sqlalchemy.orm import Session

from src.availability import Availability
from src.availability.schemas import AvailabilityRead, AvailabilityCreate, AvailabilityUpdate
from src.bookings import Booking
from src.core.db import get_db
from src.providers import Provider

router = APIRouter(prefix="/availability", tags=["Availability"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=AvailabilityRead)
async def create_slot(payload: AvailabilityCreate, db_session: Session = Depends(get_db)):
    is_valid_slot = payload.end_time > payload.start_time
    if not is_valid_slot:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Time range is not valid for a slot")

    provider = db_session.query(Provider).filter(Provider.id == payload.provider_id).first()
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found",
        )

    overlapping = (
        db_session.query(Availability)
        .filter(
            Availability.provider_id == payload.provider_id,
            Availability.date == payload.date,
            payload.start_time < Availability.end_time,
            payload.end_time > Availability.start_time,
        )
        .first()
    )
    if overlapping:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Overlapping slot already exists",
        )

    slot = Availability(
        provider_id=payload.provider_id,
        date=payload.date,
        start_time=payload.start_time,
        end_time=payload.end_time,
        is_booked=False,
    )

    db_session.add(slot)
    db_session.commit()
    db_session.refresh(slot)
    return slot

@router.get("/", response_model=List[AvailabilityRead], status_code=status.HTTP_200_OK)
def get_slots(
    provider_id: int = Query(..., ge=1),
    date: Optional[date] = Query(None),
    only_free: bool = Query(False),
    db_session: Session = Depends(get_db),
):
    q = db_session.query(Availability).filter(Availability.provider_id == provider_id)

    if date is not None:
        q = q.filter(Availability.date == date)

    if only_free:
        q = q.filter(Availability.is_booked.is_(False))

    slots = q.order_by(Availability.date.asc(), Availability.start_time.asc()).all()
    return slots


@router.patch("/{slot_id}", response_model=AvailabilityRead, status_code=status.HTTP_200_OK)
def update_slot(
    slot_id: int,
    payload: AvailabilityUpdate,
    db_session: Session = Depends(get_db),
):
    slot = db_session.query(Availability).filter(Availability.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot not found")

    # prevent time edits if already booked
    if slot.is_booked and (
        payload.date is not None or payload.start_time is not None or payload.end_time is not None
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot change date/time of a booked slot",
        )

    update_data = payload.model_dump(exclude_unset=True)

    new_date = update_data.get("date", slot.date)
    new_start = update_data.get("start_time", slot.start_time)
    new_end = update_data.get("end_time", slot.end_time)
    new_provider_id = update_data.get("provider_id", slot.provider_id)

    if new_end <= new_start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Time range is not valid for a slot",
        )

    overlap = (
        db_session.query(Availability)
        .filter(
            Availability.id != slot_id,
            Availability.provider_id == new_provider_id,
            Availability.date == new_date,
            new_start < Availability.end_time,
            new_end > Availability.start_time,
        )
        .first()
    )
    if overlap:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Overlapping slot already exists",
        )

    for field, value in update_data.items():
        setattr(slot, field, value)

    db_session.commit()
    db_session.refresh(slot)
    return slot


@router.delete("/{slot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_slot(slot_id: int, db_session: Session = Depends(get_db)):
    slot = db_session.query(Availability).filter(Availability.id == slot_id).first()
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slot not found"
        )

    if slot.is_booked:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete a booked slot",
        )

    has_booking_reference = (
        db_session.query(Booking.id)
        .filter(Booking.availability_id == slot_id)
        .first()
    )
    if has_booking_reference:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete slot because it is linked to booking(s)"
        )

    db_session.delete(slot)
    db_session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)