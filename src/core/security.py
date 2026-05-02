import bcrypt
import hmac
import hashlib
from src.core.config import settings


class Security:

    DEFAULT_BCRYPT_ROUNDS = 12

    @staticmethod
    def hash_password(password: str, rounds: int = DEFAULT_BCRYPT_ROUNDS) -> str:
        if not password:
            raise ValueError("Password must not be empty.")
        salt = bcrypt.gensalt(rounds=rounds)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        if not plain_password or not hashed_password:
            return False
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )


    @staticmethod
    def otp_hash(email: str, code: str) -> str:
        msg = f"{email}:{code}".encode("utf-8")
        secret = settings.SECRET_KEY.encode("utf-8")
        return hmac.new(secret, msg, hashlib.sha256).hexdigest()
