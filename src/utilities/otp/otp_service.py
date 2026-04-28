import hmac
import hashlib
import secrets

from src.core.config import settings
from src.core.redis import redis_client

OTP_TTL_SECONDS = 10 * 60
OTP_COOLDOWN_SECONDS = 60
OTP_MAX_ATTEMPTS = 5
#TODO : move these to env later

KEY_OTP = "otp:email_verify:{user_id}"
KEY_ATTEMPTS = "otp:email_verify_attempts:{user_id}"
KEY_COOLDOWN = "otp:email_verify_cooldown:{user_id}"


def _otp_hash(user_id: int, code: str) -> str:
    msg = f"{user_id}:{code}".encode("utf-8")
    secret = settings.SECRET_KEY.encode("utf-8")
    return hmac.new(secret, msg, hashlib.sha256).hexdigest()


def generate_otp_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def set_email_verification_otp(user_id: int) -> str:
    cooldown_key = KEY_COOLDOWN.format(user_id=user_id)
    if redis_client.exists(cooldown_key):
        raise ValueError("OTP recently sent. Please wait before requesting another code.")

    code = generate_otp_code()
    code_hash = _otp_hash(user_id, code)

    otp_key = KEY_OTP.format(user_id=user_id)
    attempts_key = KEY_ATTEMPTS.format(user_id=user_id)

    pipe = redis_client.pipeline()
    pipe.setex(otp_key, OTP_TTL_SECONDS, code_hash)
    pipe.setex(attempts_key, OTP_TTL_SECONDS, 0)
    pipe.setex(cooldown_key, OTP_COOLDOWN_SECONDS, 1)
    pipe.execute()

    return code

def verify_email_verification_otp(user_id: int, code: str) -> None:
    """
    Verifies OTP stored in Redis.
    Raises ValueError with a safe message if invalid/expired/too many attempts.
    """
    otp_key = KEY_OTP.format(user_id=user_id)
    attempts_key = KEY_ATTEMPTS.format(user_id=user_id)

    stored_hash = redis_client.get(otp_key)
    if not stored_hash:
        raise ValueError("OTP is expired or not requested")

    # attempts
    attempts_raw = redis_client.get(attempts_key)
    attempts = int(attempts_raw or 0)
    if attempts >= OTP_MAX_ATTEMPTS:
        raise ValueError("Too many attempts. Please request a new OTP")

    incoming_hash = _otp_hash(user_id, code)

    if not hmac.compare_digest(stored_hash, incoming_hash):
        redis_client.incr(attempts_key)
        raise ValueError("Invalid OTP code")

    redis_client.delete(
        otp_key,
        attempts_key,
        KEY_COOLDOWN.format(user_id=user_id),
    )