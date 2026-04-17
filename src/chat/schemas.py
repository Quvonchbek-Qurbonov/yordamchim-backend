from datetime import datetime
from typing import Annotated, Text

from pydantic import BaseModel, Field


class ChatLogCreate(BaseModel):
    message: Annotated[Text, Field(max_length=5000)]


class ChatLogRead(BaseModel):
    id: int
    user_id: int
    message: Annotated[Text, Field(max_length=5000)]
    response: Annotated[Text, Field(max_length=5000)]

    created_at: datetime