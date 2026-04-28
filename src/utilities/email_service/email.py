from __future__ import annotations

import logging
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

from src.core.config import settings
from src.utilities.email_service.otp_template import EmailContent

logger = logging.getLogger(__name__)


def _brevo_client() -> sib_api_v3_sdk.TransactionalEmailsApi:
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key["api-key"] = settings.BREVO_API_KEY
    return sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))


def send_brevo_email(to_email: str, content: EmailContent) -> None:
    api_instance = _brevo_client()

    sender = {"name": settings.SENDER_NAME, "email": settings.SENDER_EMAIL}
    to = [{"email": to_email}]

    email = sib_api_v3_sdk.SendSmtpEmail(
        to=to,
        sender=sender,
        subject=content.subject,
        html_content=content.html,
        text_content=content.text,
    )

    try:
        api_instance.send_transac_email(email)
    except ApiException as e:
        logger.exception("Brevo send_transac_email failed: %s", getattr(e, "body", str(e)))
        raise