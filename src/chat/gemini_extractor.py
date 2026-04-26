from google import genai
from sqlalchemy.orm import Session

from src.core.config import settings
from src.chat.schemas import ServiceGemini

from datetime import datetime

from src.services.schemas import ServiceRead
from src.services.service import get_all_services


current_datetime = datetime.now().isoformat()

client = genai.Client(api_key=settings.GEMINI_API_KEY)


def choose_service(text: str, db_session: Session):
    service_selection_prompt = """
        You should choose a service from listed services (as json) according to user text and recommend that service to user.
        If you are strongly unsure to select, add question to clarification_question field. Otherwise set it empty.
        "response" field is for recommendation. If you have clarification_question and not confident, set "response" empty.
        Return only requested fields.
    """

    services = [ServiceRead.model_validate(service) for service in get_all_services(db_session)]

    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[service_selection_prompt, f"User: {text}", f"Services: {services}"],
        config={
            "temperature": 0,
            "response_mime_type": "application/json",
            "response_schema": ServiceGemini,
        },
    )

    return resp.parsed