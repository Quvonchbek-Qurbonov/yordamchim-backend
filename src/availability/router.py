from typing import Optional, List
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from sqlalchemy.orm import Session

from src.core.db import get_db
from src.auth.dependencies import get_current_user
from src.users.models import User, Roles
from src.availability.models import Availability
from src.availability.schemas import AvailabilityRead, AvailabilityCreate, AvailabilityUpdate
from src.bookings.models import Booking

router = APIRouter(prefix="/availability", tags=["Availability"])


def _ensure_provider_or_admin(current_user: User) -> None:
    if current_user.role not in {Roles.provider, Roles.admin}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only providers or admins can manage availability",
        )


def _can_manage_provider_slots(current_user: User, provider_user_id: int) -> None:
    if current_user.role == Roles.admin:
        return
    if current_user.role == Roles.provider and current_user.id == provider_user_id:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You cannot manage another provider's availability",
    )


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=AvailabilityRead)
def create_slot(
    payload: AvailabilityCreate,
    db_session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_provider_or_admin(current_user)
    _can_manage_provider_slots(current_user, payload.provider_id)

    if payload.end_time <= payload.start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Time range is not valid for a slot",
        )

    provider_user = (
        db_session.query(User)
        .filter(User.id == payload.provider_id, User.role == Roles.provider, User.is_active.is_(True))
        .first()
    )
    if not provider_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found",
        )

    overlapping = (
        db_session.query(Availability)
        .filter(
            Availability.user_id == payload.provider_id,
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
        user_id=payload.provider_id,
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
    provider_user_id: int = Query(..., ge=1),
    date_filter: Optional[date] = Query(None, alias="date"),
    only_free: bool = Query(False),
    db_session: Session = Depends(get_db),
):
    q = db_session.query(Availability).filter(Availability.user_id == provider_user_id)

    if date_filter is not None:
        q = q.filter(Availability.date == date_filter)

    if only_free:
        q = q.filter(Availability.is_booked.is_(False))

    slots = q.order_by(Availability.date.asc(), Availability.start_time.asc()).all()
    return slots


@router.patch("/{slot_id}", response_model=AvailabilityRead, status_code=status.HTTP_200_OK)
def update_slot(
    slot_id: int,
    payload: AvailabilityUpdate,
    db_session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_provider_or_admin(current_user)

    slot = db_session.query(Availability).filter(Availability.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot not found")

    _can_manage_provider_slots(current_user, slot.user_id)

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
    new_user_id = update_data.get("user_id", slot.user_id)

    if new_end <= new_start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Time range is not valid for a slot",
        )

    # if reassigning slot owner, enforce authorization + provider validity
    if new_user_id != slot.user_id:
        _can_manage_provider_slots(current_user, new_user_id)
        provider_user = (
            db_session.query(User)
            .filter(User.id == new_user_id, User.role == Roles.provider, User.is_active.is_(True))
            .first()
        )
        if not provider_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target provider user not found",
            )

    overlap = (
        db_session.query(Availability)
        .filter(
            Availability.id != slot_id,
            Availability.user_id == new_user_id,
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
def delete_slot(
    slot_id: int,
    db_session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_provider_or_admin(current_user)

    slot = db_session.query(Availability).filter(Availability.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot not found")

    _can_manage_provider_slots(current_user, slot.user_id)

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
            detail="Cannot delete slot because it is linked to booking(s)",
        )

    db_session.delete(slot)
    db_session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)