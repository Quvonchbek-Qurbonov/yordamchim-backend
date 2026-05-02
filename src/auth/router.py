from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from sqlalchemy import or_

from src.auth.schemas import LoginRequest, RefreshRequest, TokenPair, UserCreate
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.db import get_db
from src.users.models import User, Roles
from src.auth.jwt_handler import JwtAuth, TokenType
from src.core.security import Security
from src.utilities.email_service import send_brevo_email
from src.utilities.email_service.otp_template import otp_email
from src.utilities.otp.otp_service import OtpService

from src.auth.schemas import VerifyOtpRequest, RegistrationRead
from src.auth.registration import set_pending_registration, get_pending_registration, delete_pending_registration

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, background_tasks: BackgroundTasks, db_session: Session = Depends(get_db)):

    if payload.role not in [Roles.user, Roles.provider]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User can not be registered")

    existing_user = db_session.query(User).filter(
        or_(User.email == payload.email, User.phone == payload.phone)
    ).first()

    if existing_user:
        if existing_user.email == payload.email:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
        if existing_user.phone == payload.phone:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone already exists")
    pass

    pending_data = {
        "email": payload.email,
        "name": payload.name,
        "phone": payload.phone,
        "role": payload.role.value,
        "password": Security.hash_password(payload.password),
    }
    set_pending_registration(payload.email, pending_data)

    #Creating otp code and strong to Redis
    try:
        code = OtpService.set_email_verification_otp(payload.email)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))

    #Sending Otp code
    content = otp_email(code=code, expires_minutes=settings.PENDING_REG_TTL_SECONDS // 60)
    background_tasks.add_task(send_brevo_email, payload.email, content)

    return {"detail": "Verification code sent successfully"}


@router.post("/verify", status_code=status.HTTP_200_OK, response_model=RegistrationRead)
def verify(payload: VerifyOtpRequest, db_session: Session = Depends(get_db)):

    try:
        OtpService.verify_email_verification_otp(payload.email, payload.code)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Otp verification failed")

    pending = get_pending_registration(payload.email)
    if not pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration data expired. Please register again.",
        )
    existing_user = (
        db_session.query(User)
        .filter(or_(User.email == pending["email"], User.phone == pending["phone"]))
        .first()
    )
    if existing_user:
        delete_pending_registration(payload.email)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")

    role = pending["role"]
    verification = False
    if role == Roles.user:
        verification = True

    user = User(
        email=pending["email"],
        name=pending["name"],
        phone=pending["phone"],
        password=pending["password"],
        role=pending["role"],  # or Roles(pending["role"])
        is_verified=verification,
        is_active=True,
    )
    print(user)

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    delete_pending_registration(payload.email)

    return user


@router.post("/login", response_model=TokenPair)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not Security.verify_password(payload.password, str(user.password)):
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


