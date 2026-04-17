from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session, joinedload
from typing import List

from src.availability import Availability
from src.bookings import Booking
from src.core.db import get_db
from src.providers import Provider
from src.providers.schemas import ProviderUpdate, ProviderRead, ProviderCreate
from src.services import Service

router = APIRouter(prefix="/providers", tags=["Providers"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ProviderRead)
async def create_provider(payload: ProviderCreate, db_session: Session = Depends(get_db)):
    phone_exists = db_session.query(Provider).filter(Provider.phone == payload.phone).first()
    if phone_exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This provider with that phone already exists")

    service_exits = db_session.query(Service).filter(Service.id == payload.service_id).first()
    if not service_exits:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service does not exist with given id")

    provider = Provider(
        name=payload.name,
        phone=payload.phone,
        service_id=payload.service_id
    )
    db_session.add(provider)
    db_session.commit()
    db_session.refresh(provider)
    provider = (
        db_session.query(Provider)
        .options(joinedload(Provider.service))
        .filter(Provider.id == provider.id)
        .first()
    )
    return provider


@router.get("/", status_code=status.HTTP_200_OK, response_model=List[ProviderRead])
async def list_providers(service_id: int | None = None, skip: int = Query(0, ge=0),
                         limit: int = Query(10, ge=1, le=100), db_session: Session = Depends(get_db)):
    providers = db_session.query(Provider).options(joinedload(Provider.service)).offset(skip).limit(limit).all()
    return providers


@router.get("/{provider_id}", status_code=status.HTTP_200_OK, response_model=ProviderRead)
async def get_provider(provider_id: int, db_session: Session = Depends(get_db)):
    provider = db_session.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This provider does not exist")
    return provider


@router.patch("/{provider_id}", status_code=status.HTTP_200_OK, response_model=ProviderRead)
async def update_provider(provider_id: int, payload: ProviderUpdate, db_session: Session = Depends(get_db)):
    provider = db_session.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This provider does not exist")

    service_exists = db_session.query(Service).filter(Service.id == payload.service_id).first()
    if not service_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service does not exist with given id")

    update_data  = payload.model_dump(exclude_unset=True)
    if not update_data:
        return provider

    for key, value in update_data.items():
        setattr(provider, key, value)

    db_session.add(provider)
    db_session.commit()
    db_session.refresh(provider)

    provider = (
        db_session.query(Provider)
        .options(joinedload(Provider.service))
        .filter(Provider.id == provider.id)
        .first()
    )
    return provider




@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_provider(provider_id: int, db_session: Session = Depends(get_db)):
    provider = db_session.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This provider does not exist"
        )

    has_bookings = db_session.query(Booking.id).filter(Booking.provider_id == provider_id).first()
    has_availability = db_session.query(Availability.id).filter(Availability.provider_id == provider_id).first()

    if has_bookings or has_availability:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete provider because it is used by other records"
        )

    db_session.delete(provider)
    db_session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)