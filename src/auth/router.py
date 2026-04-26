from fastapi import APIRouter, HTTPException, status, Depends

from src.auth.schemas import LoginRequest, RefreshRequest, TokenPair
from sqlalchemy.orm import Session

from src.core.db import get_db
from src.users.models import User
from src.auth.jwt_handler import JwtAuth, TokenType
from src.core.security import verify_password


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenPair)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, str(user.password)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    sub = str(user.id)
    return TokenPair(
        access_token=JwtAuth.create_access_token(subject=sub, extra_claims={"role": user.role.value}),
        refresh_token=JwtAuth.create_refresh_token(subject=sub, extra_claims={"role": user.role.value})
    )


@router.post("/refresh", response_model=TokenPair)
def refresh_token(payload: RefreshRequest, db: Session = Depends(get_db)):
    user_id = JwtAuth.get_subject_from_token(payload.refresh_token, expected_type=TokenType.REFRESH)
    user = db.query(User).filter(User.id == user_id).first()

    sub = str(user.id)
    role = user.role.value
    return TokenPair(
        access_token=JwtAuth.create_access_token(subject=sub, extra_claims={"role": role}),
        refresh_token=JwtAuth.create_refresh_token(subject=sub, extra_claims={"role": role})
    )