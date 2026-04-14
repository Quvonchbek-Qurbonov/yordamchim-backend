from fastapi import APIRouter

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/")
async def process_message():
    pass