from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from src.bookings import Booking
from src.core.db import get_db
from src.users.schemas import UserRead, UserCreate, UserUpdate
from src.users import User
from src.core.security import hash_password

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserRead)
def create_user(payload: UserCreate, db_session: Session = Depends(get_db)):
    exists = db_session.query(User).filter(User.email == payload.email).first()
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

    user = User(
        email=payload.email,
        name=payload.name,
        phone=payload.phone,
        password=hash_password(payload.password),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@router.get("/{user_id}", status_code=status.HTTP_200_OK, response_model=UserRead)
def get_user(user_id: int, db_session: Session = Depends(get_db)):
    user = db_session.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.get("/", status_code=status.HTTP_200_OK, response_model=List[UserRead])
def list_users(db_session: Session = Depends(get_db)):
    return db_session.query(User).all()


@router.patch("/{user_id}", status_code=status.HTTP_200_OK, response_model=UserRead)
def update_user(user_id: int, payload: UserUpdate, db_session: Session = Depends(get_db)):
    user = db_session.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    update_data = payload.model_dump(exclude_unset=True)

    if not update_data:
        return user

    for field, value in update_data.items():
        setattr(user, field, value)

    db_session.commit()
    db_session.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db_session: Session = Depends(get_db)):
    user = db_session.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    has_bookings = db_session.query(Booking.id).filter(Booking.user_id == user_id).first()
    if has_bookings:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete user because user has related bookings"
        )

    db_session.delete(user)
    db_session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)