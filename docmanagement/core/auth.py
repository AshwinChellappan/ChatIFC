from fastapi import Depends, HTTPException, status
from typing import Any
from models.user import User
from services.azure_ad_auth_service import authorize


class ForbiddenAccess(HTTPException):
    def __init__(self, detail: Any = None) -> None:
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail, headers={"WWW-Authenticate": "Bearer"})


def get_current_user(user: User = Depends(authorize)) -> User:
    return user

