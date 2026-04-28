from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks

from src.auth.dependencies import get_current_user
from src.auth.schemas import LoginRequest, RefreshRequest, TokenPair
from sqlalchemy.orm import Session

from src.core.db import get_db
from src.users.models import User
from src.auth.jwt_handler import JwtAuth, TokenType
from src.core.security import verify_password
from src.utilities.email_service import send_brevo_email
from src.utilities.email_service.otp_template import otp_email
from src.utilities.otp.otp_service import set_email_verification_otp, OTP_TTL_SECONDS

from src.auth.schemas import VerifyOtpRequest
from src.utilities.otp.otp_service import verify_email_verification_otp


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


@router.post("/request-otp", status_code=status.HTTP_200_OK)
def send_verification_code(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    if current_user.is_verified:
        return {"detail": "Account is already verified"}

    try:
        code = set_email_verification_otp(current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))

    content = otp_email(code=code, expires_minutes=OTP_TTL_SECONDS // 60)

    background_tasks.add_task(send_brevo_email, current_user.email, content)

    return {"detail": "Verification code sent"}


@router.post("/verify-otp", status_code=status.HTTP_200_OK)
def verify_otp(
    payload: VerifyOtpRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.is_verified:
        return {"detail": "Account is already verified"}

    try:
        verify_email_verification_otp(current_user.id, payload.code)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # mark verified in DB
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.is_verified = True
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"detail": "Account verified successfully"}


