from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from src.users import User


def existence_email_phone(db_session: Session, email: str, phone: str):
    existing_user = db_session.query(User).filter(
        or_(User.email == email, User.phone == phone)
    ).first()

    if existing_user:
        if existing_user.email == email:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
        if existing_user.phone == phone:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone already exists")
    pass