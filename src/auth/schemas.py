from typing import Annotated
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, StringConstraints

from src.users.models import Roles


class UserCreate(BaseModel):
    email: EmailStr
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=50)]
    phone: Annotated[str, StringConstraints(
        strip_whitespace=True,
        min_length=7,
        max_length=20,
        pattern=r"^\+?[0-9\s\-\(\)]{7,20}$"
    )]
    role: Roles
    password: Annotated[str, StringConstraints(min_length=8, max_length=64)]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class VerifyOtpRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


class RegistrationRead(BaseModel):
    id: int
    email: EmailStr
    name: str
    phone: str
    role: Roles
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime