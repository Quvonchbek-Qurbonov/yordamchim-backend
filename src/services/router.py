from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.core.db import get_db
from src.auth.dependencies import only_admin
from src.bookings.models import Booking
from src.services.models import Service
from src.providers import ProviderService
from src.services.schemas import ServiceCreate, ServiceUpdate, ServiceRead
from src.services.service import get_all_services

router = APIRouter(prefix="/services", tags=["Services"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ServiceRead)
def create_service(
    payload: ServiceCreate,
    db_session: Session = Depends(get_db),
    _ = Depends(only_admin)
):

    normalized_name = payload.name.strip()
    if not normalized_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Service name cannot be empty")

    exists = (
        db_session.query(Service)
        .filter(func.lower(Service.name) == normalized_name.lower())
        .first()
    )
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Service already exists")

    service = Service(name=normalized_name, description=payload.description)
    db_session.add(service)
    db_session.commit()
    db_session.refresh(service)
    return service


@router.get("/", status_code=status.HTTP_200_OK, response_model=List[ServiceRead])
def list_services(skip: int = Query(0, ge=0),
                  limit: int = Query(10, ge=1, le=100), db_session: Session = Depends(get_db)):
    return get_all_services(db_session, skip=skip, limit=limit)


@router.get("/{service_id}", status_code=status.HTTP_200_OK, response_model=ServiceRead)
def get_service(service_id: int, db_session: Session = Depends(get_db)):
    service = db_session.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    return service


@router.patch("/{service_id}", status_code=status.HTTP_200_OK, response_model=ServiceRead)
def update_service(
    service_id: int,
    payload: ServiceUpdate,
    db_session: Session = Depends(get_db),
    _ = Depends(only_admin)
):

    service = db_session.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        return service

    if "name" in update_data and update_data["name"] is not None:
        new_name = update_data["name"].strip()
        if not new_name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Service name cannot be empty")

        exists = (
            db_session.query(Service)
            .filter(func.lower(Service.name) == new_name.lower(), Service.id != service_id)
            .first()
        )
        if exists:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Service already exists")

        update_data["name"] = new_name

    for key, value in update_data.items():
        setattr(service, key, value)

    db_session.commit()
    db_session.refresh(service)
    return service


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(
    service_id: int,
    db_session: Session = Depends(get_db),
    _ = Depends(only_admin)
):

    service = db_session.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")

    used_by_provider = (
        db_session.query(ProviderService.id)
        .filter(ProviderService.service_id == service_id)
        .first()
    )
    used_by_booking = (
        db_session.query(Booking.id)
        .filter(Booking.service_id == service_id)
        .first()
    )

    if used_by_provider or used_by_booking:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete service because it is used by other records",
        )

    db_session.delete(service)
    db_session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)