from typing import Annotated

from pydantic import BaseModel, StringConstraints, ConfigDict


class ServiceRead(BaseModel):
    id: int
    name: str
    description: str

    model_config = ConfigDict(from_attributes=True)


class ServiceCreate(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=50)]
    description: Annotated[str, StringConstraints(min_length=2, max_length=200)]


class ServiceUpdate(ServiceCreate):
    pass