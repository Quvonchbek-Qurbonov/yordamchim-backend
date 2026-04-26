from datetime import datetime
from typing import Annotated, Text, Optional

from pydantic import BaseModel, Field


class ChatLogCreate(BaseModel):
    message: Annotated[Text, Field(max_length=5000)]


class ChatLogRead(BaseModel):
    id: int
    user_id: int
    message: Annotated[Text, Field(max_length=5000)]
    response: Annotated[Text, Field(max_length=5000)]

    created_at: datetime


class ExtractRequest(BaseModel):
    text: str = Field(min_length=2, max_length=1000)


class ServiceGemini(BaseModel):
    confident: bool
    clarification_question: str = Field(min_length=0, max_length=1000)
    response: str = Field(min_length=0, max_length=1000)
    service_id: int