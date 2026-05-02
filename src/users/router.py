from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.params import Query
from sqlalchemy.orm import Session

from src.auth.dependencies import get_current_user, only_admin
from src.bookings import Booking
from src.core.db import get_db
from src.users.models import Roles
from src.users.schemas import UserRead, UserUpdate
from src.users import User


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/{user_id}", status_code=status.HTTP_200_OK, response_model=UserRead)
def get_user(user_id: int, db_session: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    if int(current_user.id) == user_id or current_user.role.value == Roles.admin.value:
        user = db_session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to perform this action")


@router.get("/", status_code=status.HTTP_200_OK, response_model=List[UserRead])
def list_users(skip: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100),
               role: Roles = Query(default=None), db_session: Session = Depends(get_db),
               _ = Depends(only_admin)
               ):
    if role is not None:
        return db_session.query(User).filter(User.role==role).offset(skip).limit(limit).all()
    return db_session.query(User).offset(skip).limit(limit).all()


@router.patch("/{user_id}", status_code=status.HTTP_200_OK, response_model=UserRead)
def update_user(user_id: int, payload: UserUpdate, db_session: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if int(current_user.id) == user_id or current_user.role.value == Roles.admin.value:
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

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to perform this action")


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db_session: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    if int(current_user.id) == user_id or current_user.role.value == Roles.admin.value:
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

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to perform this action")