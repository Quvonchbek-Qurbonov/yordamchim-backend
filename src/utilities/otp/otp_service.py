import hmac
import secrets
from fastapi import HTTPException

from src.core.config import settings
from src.core.redis import RedisService
from src.core.security import Security


KEY_OTP = "otp:email_verify:{email}"
KEY_ATTEMPTS = "otp:email_verify_attempts:{email}"
KEY_COOLDOWN = "otp:email_verify_cooldown:{email}"

redis_client = RedisService().client()


class OtpService:

    @staticmethod
    def generate_otp_code() -> str:
        return f"{secrets.randbelow(1_000_000):06d}"

    @staticmethod
    def set_email_verification_otp(email: str) -> str:
        cooldown_key = KEY_COOLDOWN.format(email=email)
        if redis_client.exists(cooldown_key):
            raise ValueError("OTP recently sent. Please wait before requesting another code.")

        code = OtpService.generate_otp_code()
        code_hash = Security.otp_hash(email, code)

        otp_key = KEY_OTP.format(email=email)
        attempts_key = KEY_ATTEMPTS.format(email=email)

        pipe = redis_client.pipeline()
        pipe.setex(otp_key, settings.OTP_TTL_SECONDS, code_hash)
        pipe.setex(attempts_key, settings.OTP_TTL_SECONDS, 0)
        pipe.setex(cooldown_key, settings.OTP_COOLDOWN_SECONDS, 1)
        pipe.execute()

        return code

    @staticmethod
    def verify_email_verification_otp(email: str, code: str) -> None:

        otp_key = KEY_OTP.format(email=email)
        attempts_key = KEY_ATTEMPTS.format(email=email)

        stored_hash = redis_client.get(otp_key)
        if not stored_hash:
            raise ValueError("OTP is expired or not requested")

        attempts_raw = redis_client.get(attempts_key)
        attempts = int(attempts_raw or 0)
        if attempts >= settings.OTP_MAX_ATTEMPTS:
            raise ValueError("Too many attempts. Please request a new OTP")

        incoming_hash = Security.otp_hash(email, code)

        if not hmac.compare_digest(stored_hash, incoming_hash):
            redis_client.incr(attempts_key)
            raise ValueError("Invalid OTP code")

        redis_client.delete(
            otp_key,
            attempts_key,
            KEY_COOLDOWN.format(email=email),
        )