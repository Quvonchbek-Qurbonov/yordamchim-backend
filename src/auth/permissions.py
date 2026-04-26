from fastapi import Depends, HTTPException, status
from typing import Callable
from src.auth.dependencies import get_current_user
from src.users.models import User


def require_roles(*allowed_roles: str) -> Callable:
    def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource",
            )
        return current_user
    return checker