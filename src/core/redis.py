from redis import Redis
from src.core.config import settings


class RedisService:

    @staticmethod
    def client() -> Redis:
        return Redis.from_url(settings.REDIS_URL, decode_responses=True)