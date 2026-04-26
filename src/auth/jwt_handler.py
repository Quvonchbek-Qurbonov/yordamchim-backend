from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from fastapi import HTTPException, status

from src.core.config import settings


SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS


class TokenType:
    ACCESS = "access"
    REFRESH = "refresh"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

class JwtAuth:

    @staticmethod
    def create_token(
        subject: str,
        token_type: str,
        expires_delta: timedelta,
        extra_claims: Optional[Dict[str, Any]] = None,
    ) -> str:
        now = _utcnow()
        payload: Dict[str, Any] = {
            "sub": subject,
            "type": token_type,
            "iat": int(now.timestamp()),
            "exp": int((now + expires_delta).timestamp()),
        }
        if extra_claims:
            payload.update(extra_claims)

        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def create_access_token(subject: str, extra_claims: Optional[Dict[str, Any]] = None) -> str:
        return JwtAuth.create_token(
            subject=subject,
            token_type=TokenType.ACCESS,
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            extra_claims=extra_claims,
        )


    @staticmethod
    def create_refresh_token(subject: str, extra_claims: Optional[Dict[str, Any]] = None) -> str:
        return JwtAuth.create_token(
            subject=subject,
            token_type=TokenType.REFRESH,
            expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            extra_claims=extra_claims,
        )

    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

    @staticmethod
    def verify_token_type(payload: Dict[str, Any], expected_type: str) -> None:
        if payload.get("type") != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type, expected '{expected_type}'",
            )

    @staticmethod
    def get_subject_from_token(token: str, expected_type: str = TokenType.ACCESS) -> str:
        payload = JwtAuth.decode_token(token)
        JwtAuth.verify_token_type(payload, expected_type)

        sub = payload.get("sub")
        if not sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token subject missing",
            )
        return str(sub)