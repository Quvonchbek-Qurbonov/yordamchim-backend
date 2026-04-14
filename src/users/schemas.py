from datetime import datetime
from typing import Annotated, Optional
from pydantic import BaseModel, EmailStr, StringConstraints

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
    email: EmailStr
    name: str
    phone: str
    id: int
    created_at: datetime
    updated_at: datetime