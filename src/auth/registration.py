import json
from typing import Any

from src.core.config import settings
from src.core.redis import RedisService

redis_client = RedisService().client()

KEY_PENDING = "reg:pending:{email}"


def set_pending_registration(email: str, data: dict[str, Any]) -> None:
    redis_client.setex(KEY_PENDING.format(email=email), settings.PENDING_REG_TTL_SECONDS, json.dumps(data))


def get_pending_registration(email: str) -> dict[str, Any] | None:
    raw = redis_client.get(KEY_PENDING.format(email=email))
    return json.loads(raw) if raw else None


def delete_pending_registration(email: str) -> None:
    redis_client.delete(
        KEY_PENDING.format(email=email)
    )