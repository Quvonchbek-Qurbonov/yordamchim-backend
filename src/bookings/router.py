from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session, joinedload

from src.core.db import get_db
from src.auth.dependencies import get_current_user
from src.users.models import User, Roles
from src.bookings.models import Booking, BookingStatus
from src.bookings.schemas import BookingRead, BookingUpdate, BookingCreate
from src.services.models import Service
from src.availability.models import Availability
from src.providers import ProviderService

router = APIRouter(prefix="/bookings", tags=["Bookings"])


def _can_access_booking(current_user: User, booking: Booking) -> bool:
    if current_user.role == Roles.admin:
        return True
    if booking.user_id == current_user.id:
        return True
    if booking.provider_id == current_user.id:
        return True
    return False


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=BookingRead)
def create_booking(
    payload: BookingCreate,
    db_session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != Roles.admin and payload.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot create booking for another user")

    user = db_session.query(User).filter(User.id == payload.user_id, User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist")

    provider_user = (
        db_session.query(User)
        .filter(User.id == payload.provider_id, User.role == Roles.provider, User.is_active.is_(True))
        .first()
    )
    if not provider_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider does not exist")

    service = db_session.query(Service).filter(Service.id == payload.service_id).first()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service does not exist")

    provider_has_service = (
        db_session.query(ProviderService.id)
        .filter(
            ProviderService.user_id == payload.provider_id,
            ProviderService.service_id == payload.service_id,
        )
        .first()
    )
    if not provider_has_service:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected provider does not provide this service",
        )

    availability = (
        db_session.query(Availability)
        .filter(
            Availability.id == payload.availability_id,
            Availability.user_id == payload.provider_id,
        )
        .first()
    )
    if not availability:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Availability slot does not exist")

    if availability.is_booked:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slot is already booked")

    booking = Booking(
        user_id=payload.user_id,
        provider_id=payload.provider_id,
        service_id=payload.service_id,
        availability_id=payload.availability_id,
        start_at=availability.start_at,
        end_at=availability.end_at,
        status=BookingStatus.pending,
        total_price=payload.total_price,
        notes=payload.notes,
    )

    availability.is_booked = True

    db_session.add(booking)
    db_session.add(availability)
    db_session.commit()
    db_session.refresh(booking)

    booking = (
        db_session.query(Booking)
        .options(
            joinedload(Booking.user),
            joinedload(Booking.provider),
            joinedload(Booking.service),
            joinedload(Booking.availability),
        )
        .filter(Booking.id == booking.id)
        .first()
    )
    return booking


@router.get("/", status_code=status.HTTP_200_OK, response_model=List[BookingRead])
def list_bookings(
    user_id: int | None = None,
    provider_id: int | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db_session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db_session.query(Booking).options(
        joinedload(Booking.user),
        joinedload(Booking.provider),
        joinedload(Booking.service),
        joinedload(Booking.availability),
    )

    # non-admin can only see their own side of bookings
    if current_user.role != Roles.admin:
        if current_user.role == Roles.provider:
            q = q.filter(Booking.provider_id == current_user.id)
        else:
            q = q.filter(Booking.user_id == current_user.id)

    if user_id is not None:
        q = q.filter(Booking.user_id == user_id)

    if provider_id is not None:
        q = q.filter(Booking.provider_id == provider_id)

    bookings = q.order_by(Booking.id.desc()).offset(skip).limit(limit).all()
    return bookings


@router.get("/{booking_id}", status_code=status.HTTP_200_OK, response_model=BookingRead)
def get_booking(
    booking_id: int,
    db_session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = (
        db_session.query(Booking)
        .options(
            joinedload(Booking.user),
            joinedload(Booking.provider),
            joinedload(Booking.service),
            joinedload(Booking.availability),
        )
        .filter(Booking.id == booking_id)
        .first()
    )
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking does not exist")

    if not _can_access_booking(current_user, booking):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    return booking


@router.patch("/{booking_id}", status_code=status.HTTP_200_OK, response_model=BookingRead)
def update_booking_status(
    booking_id: int,
    payload: BookingUpdate,
    db_session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = db_session.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking does not exist")

    if not _can_access_booking(current_user, booking):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        booking = (
            db_session.query(Booking)
            .options(
                joinedload(Booking.user),
                joinedload(Booking.provider),
                joinedload(Booking.service),
                joinedload(Booking.availability),
            )
            .filter(Booking.id == booking.id)
            .first()
        )
        return booking

    # if booking gets cancelled, release slot
    if "status" in update_data and update_data["status"] == BookingStatus.cancelled:
        if booking.availability_id:
            slot = db_session.query(Availability).filter(Availability.id == booking.availability_id).first()
            if slot:
                slot.is_booked = False
                db_session.add(slot)

    for key, value in update_data.items():
        setattr(booking, key, value)

    db_session.add(booking)
    db_session.commit()
    db_session.refresh(booking)

    booking = (
        db_session.query(Booking)
        .options(
            joinedload(Booking.user),
            joinedload(Booking.provider),
            joinedload(Booking.service),
            joinedload(Booking.availability),
        )
        .filter(Booking.id == booking.id)
        .first()
    )
    return booking


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_booking(
    booking_id: int,
    db_session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = db_session.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking does not exist")

    if not _can_access_booking(current_user, booking):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    # free slot before delete
    if booking.availability_id:
        slot = db_session.query(Availability).filter(Availability.id == booking.availability_id).first()
        if slot:
            slot.is_booked = False
            db_session.add(slot)

    db_session.delete(booking)
    db_session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)