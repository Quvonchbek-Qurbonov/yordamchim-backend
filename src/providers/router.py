from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session, joinedload

from src.auth.dependencies import get_current_user
from src.core.db import get_db
from src.providers.models import Profile, ProviderService
from src.providers.schemas import ProfileCreate, ProfileRead, ProfileUpdate
from src.services.models import Service
from src.users.models import Roles, User
from src.bookings.models import Booking

router = APIRouter(prefix="/providers", tags=["Providers"])


def _ensure_provider_or_admin(current_user: User):
    if current_user.role not in [Roles.provider, Roles.admin]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Provider or admin privileges are required",
        )


@router.post("/profile", status_code=status.HTTP_201_CREATED, response_model=ProfileRead)
def create_profile(
    payload: ProfileCreate,
    db_session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_provider_or_admin(current_user)

    existing = db_session.query(Profile).filter(Profile.user_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Profile already exists")

    profile = Profile(
        user_id=current_user.id,
        bio=payload.bio,
        about=payload.about,
        experience_years=payload.experience_years,
        is_available=True,
        rating_avg=0,
        rating_count=0,
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)
    return profile


@router.get("/me", status_code=status.HTTP_200_OK, response_model=ProfileRead)
def get_my_profile(
    db_session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_provider_or_admin(current_user)

    profile = (
        db_session.query(Profile)
        .options(joinedload(Profile.user))
        .filter(Profile.user_id == current_user.id)
        .first()
    )
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider profile not found")
    return profile


@router.patch("/me", status_code=status.HTTP_200_OK, response_model=ProfileRead)
def update_my_profile(
    payload: ProfileUpdate,
    db_session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_provider_or_admin(current_user)

    profile = db_session.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider profile not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    db_session.commit()
    db_session.refresh(profile)
    return profile


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_profile(
    db_session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_provider_or_admin(current_user)

    profile = db_session.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider profile not found")

    has_bookings = (
        db_session.query(Booking.id)
        .filter(Booking.provider_id == current_user.id)
        .first()
    )
    if has_bookings:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete provider profile because related bookings exist",
        )

    db_session.delete(profile)
    db_session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/services/{service_id}", status_code=status.HTTP_201_CREATED)
def link_service(
    service_id: int,
    db_session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_provider_or_admin(current_user)

    service = db_session.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")

    existing_link = (
        db_session.query(ProviderService)
        .filter(
            ProviderService.user_id == current_user.id,
            ProviderService.service_id == service_id,
        )
        .first()
    )
    if existing_link:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Service already linked")

    provider_service = ProviderService(user_id=current_user.id, service_id=service_id)
    db_session.add(provider_service)
    db_session.commit()
    db_session.refresh(provider_service)

    return {
        "id": provider_service.id,
        "user_id": provider_service.user_id,
        "service_id": provider_service.service_id,
        "message": "Service linked successfully",
    }


@router.get("/services", status_code=status.HTTP_200_OK)
def list_my_services(
    db_session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_provider_or_admin(current_user)

    links = (
        db_session.query(ProviderService)
        .options(joinedload(ProviderService.service))
        .filter(ProviderService.user_id == current_user.id)
        .all()
    )

    return [
        {
            "link_id": link.id,
            "service_id": link.service_id,
            "service_name": link.service.name if link.service else None,
        }
        for link in links
    ]


@router.delete("/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def unlink_service(
    service_id: int,
    db_session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_provider_or_admin(current_user)

    link = (
        db_session.query(ProviderService)
        .filter(
            ProviderService.user_id == current_user.id,
            ProviderService.service_id == service_id,
        )
        .first()
    )
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Linked service not found")

    db_session.delete(link)
    db_session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/availability", status_code=status.HTTP_200_OK, response_model=ProfileRead)
def set_availability(
    is_available: bool = Query(...),
    db_session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_provider_or_admin(current_user)

    profile = db_session.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider profile not found")

    profile.is_available = is_available
    db_session.commit()
    db_session.refresh(profile)
    return profile


@router.get("/", status_code=status.HTTP_200_OK, response_model=List[ProfileRead])
def list_providers(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    is_available: bool | None = Query(default=None),
    db_session: Session = Depends(get_db),
):
    query = db_session.query(Profile).options(joinedload(Profile.user))

    if is_available is not None:
        query = query.filter(Profile.is_available == is_available)

    return query.offset(skip).limit(limit).all()