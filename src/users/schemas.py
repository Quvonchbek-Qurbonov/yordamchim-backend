from datetime import datetime
from typing import Annotated, Optional
from pydantic import BaseModel, EmailStr, StringConstraints, ConfigDict

from src.providers.schemas import ProfileRead
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
    password: Annotated[str, StringConstraints(min_length=8, max_length=64)]


class UserUpdate(BaseModel):
    name: Optional[Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=50)]] = None


class UserRead(BaseModel):
    id: int
    email: EmailStr
    name: str
    phone: str
    role: Roles
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime


class ProviderUserRead(BaseModel):
    user: UserRead
    profile: Optional[ProfileRead] = None

    model_config = ConfigDict(from_attributes=True)