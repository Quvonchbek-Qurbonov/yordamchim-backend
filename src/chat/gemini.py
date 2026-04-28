from google import genai
from sqlalchemy.orm import Session
from datetime import datetime

from fastapi import HTTPException, status

from src.core.config import settings
from src.chat.schemas import ServiceGemini
from src.services.schemas import ServiceRead
from src.services.service import get_all_services


current_datetime = datetime.now().isoformat()
client = genai.Client(api_key=settings.GEMINI_API_KEY)


def choose_service(text: str, db_session: Session) -> ServiceGemini:
    service_selection_prompt = """
        You should choose a service from listed services (as json) according to user text and recommend that service to user.
        If you are strongly unsure to select, add question to clarification_question field. Otherwise set it empty.
        "response" field is for recommendation. If you have clarification_question and not confident, set "response" empty.
        Return only requested fields.
    """

    services = [ServiceRead.model_validate(service) for service in get_all_services(db_session)]

    try:
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[service_selection_prompt, f"User: {text}", f"Services: {services}"],
            config={
                "temperature": 0,
                "response_mime_type": "application/json",
                "response_schema": ServiceGemini,
            },
        )

        if not resp or not getattr(resp, "parsed", None):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI service returned an empty or invalid response."
            )

        return resp.parsed

    except HTTPException:
        raise
    except Exception as e:
        error_message = str(e)

        if "429" in error_message or "RESOURCE_EXHAUSTED" in error_message:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="AI service rate limit exceeded. Please try again shortly."
            )
        if "503" in error_message:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service is temporarily unavailable due to high demand. Please try again later."
            )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI service error. We will fix it shortly"
        )