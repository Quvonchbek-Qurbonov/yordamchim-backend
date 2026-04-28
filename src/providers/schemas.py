from pydantic import BaseModel, Field, ConfigDict


class ProfileBase(BaseModel):
    bio: str | None = Field(default=None, max_length=500)
    about: str | None = Field(default=None, max_length=1000)
    experience_years: int | None = Field(default=None, ge=0, le=80)


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(BaseModel):
    bio: str | None = Field(default=None, max_length=500)
    about: str | None = Field(default=None, max_length=1000)
    experience_years: int | None = Field(default=None, ge=0, le=80)
    is_available: bool | None = None


class ProfileRead(BaseModel):
    id: int
    user_id: int
    bio: str | None
    about: str | None
    experience_years: int | None
    rating_avg: float | None
    rating_count: int | None
    is_available: bool

    model_config = ConfigDict(from_attributes=True)