from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session, joinedload

from src.core.db import get_db
from src.bookings.models import Booking, BookingStatus
from src.bookings.schemas import BookingRead, BookingUpdate, BookingCreate
from src.users import User
from src.providers import Provider
from src.services import Service
from src.availability import Availability

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=BookingRead)
async def create_booking(payload: BookingCreate, db_session: Session = Depends(get_db)):
    user = db_session.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist")

    provider = db_session.query(Provider).filter(Provider.id == payload.provider_id).first()
    if not provider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider does not exist")

    service = db_session.query(Service).filter(Service.id == payload.service_id).first()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service does not exist")

    availability = (
        db_session.query(Availability)
        .filter(
            Availability.id == payload.availability_id,
            Availability.provider_id == payload.provider_id,
        )
        .first()
    )
    if not availability:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Availability slot does not exist")

    if availability.is_booked:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slot is already booked")

    if payload.end_at <= payload.start_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid booking time range")

    if provider.service_id != payload.service_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected provider does not provide this service",
        )

    booking = Booking(
        user_id=payload.user_id,
        provider_id=payload.provider_id,
        service_id=payload.service_id,
        availability_id=payload.availability_id,
        start_at=payload.start_at,
        end_at=payload.end_at,
        status=payload.status,
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
            joinedload(Booking.provider).joinedload(Provider.service),
            joinedload(Booking.service),
            joinedload(Booking.availability),
        )
        .filter(Booking.id == booking.id)
        .first()
    )
    return booking


@router.get("/", status_code=status.HTTP_200_OK, response_model=List[BookingRead])
async def list_bookings(
    user_id: int | None = None,
    provider_id: int | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db_session: Session = Depends(get_db),
):
    q = db_session.query(Booking).options(
        joinedload(Booking.user),
        joinedload(Booking.provider).joinedload(Provider.service),
        joinedload(Booking.service),
        joinedload(Booking.availability),
    )

    if user_id is not None:
        q = q.filter(Booking.user_id == user_id)

    if provider_id is not None:
        q = q.filter(Booking.provider_id == provider_id)

    bookings = q.order_by(Booking.id.desc()).offset(skip).limit(limit).all()
    return bookings


@router.get("/{booking_id}", status_code=status.HTTP_200_OK, response_model=BookingRead)
async def get_booking(booking_id: int, db_session: Session = Depends(get_db)):
    booking = (
        db_session.query(Booking)
        .options(
            joinedload(Booking.user),
            joinedload(Booking.provider).joinedload(Provider.service),
            joinedload(Booking.service),
            joinedload(Booking.availability),
        )
        .filter(Booking.id == booking_id)
        .first()
    )
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking does not exist")
    return booking


@router.patch("/{booking_id}", status_code=status.HTTP_200_OK, response_model=BookingRead)
async def update_booking_status(
    booking_id: int,
    payload: BookingUpdate,
    db_session: Session = Depends(get_db),
):
    booking = db_session.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking does not exist")

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        booking = (
            db_session.query(Booking)
            .options(
                joinedload(Booking.user),
                joinedload(Booking.provider).joinedload(Provider.service),
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
            joinedload(Booking.provider).joinedload(Provider.service),
            joinedload(Booking.service),
            joinedload(Booking.availability),
        )
        .filter(Booking.id == booking.id)
        .first()
    )
    return booking


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_booking(booking_id: int, db_session: Session = Depends(get_db)):
    booking = db_session.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking does not exist")

    # free slot before delete
    if booking.availability_id:
        slot = db_session.query(Availability).filter(Availability.id == booking.availability_id).first()
        if slot:
            slot.is_booked = False
            db_session.add(slot)

    db_session.delete(booking)
    db_session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)