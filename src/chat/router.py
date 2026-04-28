from fastapi import APIRouter, HTTPException
from fastapi.params import Depends

from sqlalchemy.orm import Session
from starlette import status

from src.auth.dependencies import get_current_user
from src.chat import ChatLog
from src.chat.schemas import ExtractRequest, ServiceGemini
from src.core.db import get_db
from src.users import User

from src.chat.gemini import choose_service


router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ServiceGemini)
async def process_message(payload: ExtractRequest, db_session: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user_id = int(current_user.id)
    user_exists = db_session.query(User).filter(User.id == user_id).first()
    if not user_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    chat_response = choose_service(payload.text, db_session)

    chat_log = chat_response.response
    if not chat_response.confident:
        chat_log = chat_response.clarification_question

    chat_log = ChatLog(
        user_id=user_id,
        message=payload.text,
        response=chat_log
    )
    db_session.add(chat_log)
    db_session.commit()

    return chat_response
