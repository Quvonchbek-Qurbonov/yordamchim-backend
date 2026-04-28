from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from src.core.db import get_db
from src.users.models import User, Roles
from src.auth.jwt_handler import JwtAuth, TokenType

bearer_scheme = HTTPBearer(auto_error=True)


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    token = creds.credentials
    user_id = JwtAuth.get_subject_from_token(token, expected_type=TokenType.ACCESS)

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    # if not user.is_verified:
    #     raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Your account is not verified. Please verify your account")
    return user


def only_admin(
        creds: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    token = creds.credentials
    role = JwtAuth.get_role_from_token(token, expected_type=TokenType.ACCESS)
    if role != Roles.admin.value:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin privilege is required")
    return role


def get_current_verified_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not verified",
        )
    return current_user