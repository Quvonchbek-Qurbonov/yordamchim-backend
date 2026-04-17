from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List

from src.bookings import Booking
from src.core.db import get_db
from src.providers import Provider
from src.services import Service
from src.services.schemas import ServiceCreate, ServiceUpdate, ServiceRead


router = APIRouter(prefix="/services", tags=["Services"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ServiceRead)
async def create_service(payload: ServiceCreate, db_session: Session = Depends(get_db)):
    exits = db_session.query(Service).filter(Service.name == payload.name).first()
    if exits:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Service already exists")
    service = Service(name=payload.name, description=payload.description)
    db_session.add(service)
    db_session.commit()
    db_session.refresh(service)
    return service




@router.get("/", status_code=status.HTTP_200_OK, response_model=List[ServiceRead])
async def list_services(db_session: Session = Depends(get_db)):
    services = db_session.query(Service).all()
    return services



@router.get("/{service_id}", status_code=status.HTTP_200_OK, response_model=ServiceRead)
async def get_service(service_id: int, db_session: Session = Depends(get_db)):
    service = db_session.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    return service


@router.patch("/{service_id}", status_code=status.HTTP_200_OK, response_model=ServiceRead)
async def update_service(service_id: int, payload: ServiceUpdate, db_session: Session = Depends(get_db)):
    service = db_session.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")

    update_data = payload.model_dump(exclude_unset=True)

    if not update_data:
        return service

    if payload.name:
        exists = db_session.query(Service).filter(Service.name == payload.name).first()
        if exists:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Service already exists")


    for key, value in update_data.items():
        setattr(service, key, value)

    db_session.commit()
    db_session.refresh(service)
    return service


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(service_id: int, db_session: Session = Depends(get_db)):
    service = db_session.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )

    used_by_provider = db_session.query(Provider.id).filter(Provider.service_id == service_id).first()
    used_by_booking = db_session.query(Booking.id).filter(Booking.service_id == service_id).first()

    if used_by_provider or used_by_booking:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete service because it is used by other records"
        )

    db_session.delete(service)
    db_session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
