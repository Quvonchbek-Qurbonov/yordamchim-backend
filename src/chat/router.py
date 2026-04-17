from fastapi import APIRouter, HTTPException
from fastapi.params import Depends

from sqlalchemy.orm import Session
from starlette import status

from src.chat import ChatLog
from src.chat.schemas import ChatLogCreate, ChatLogRead
from src.core.db import get_db
from src.users import User

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/{user_id}", status_code=status.HTTP_201_CREATED)
async def process_message(user_id: int, payload: ChatLogCreate, db_session: Session = Depends(get_db)):
    user_exists = db_session.query(User).filter(User.id == user_id).first()
    if not user_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    chat_response = "Currently not available"
    chat_log = ChatLog(user_id=user_id, message=payload.message, response=chat_response)
    db_session.add(chat_log)
    db_session.commit()
    return chat_response
