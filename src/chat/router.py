from fastapi import APIRouter, HTTPException
from fastapi.params import Depends

from sqlalchemy.orm import Session
from starlette import status

from src.chat.schemas import ExtractRequest
from src.core.db import get_db
from src.users import User

from src.chat.gemini_extractor import choose_service


router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/{user_id}", status_code=status.HTTP_201_CREATED)
async def process_message(user_id: int, payload: ExtractRequest, db_session: Session = Depends(get_db)):
    user_exists = db_session.query(User).filter(User.id == user_id).first()
    if not user_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    chat_response = choose_service(payload.text, db_session)
    return chat_response
