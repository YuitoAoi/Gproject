"""获取当前用户信息服务。"""
import uuid
from datetime import datetime

from pydantic import BaseModel

from src.services.interfaces.user_repository import UserRepository


class UserInfoResponse(BaseModel):
    """用户信息响应（不含密码）。"""
    id: uuid.UUID
    name: str
    email: str
    is_admin: bool
    is_active: bool
    created_at: datetime
    last_login: datetime
    error: str | None = None


class UserGetService:
    """获取当前用户信息用例。"""

    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    def execute(self, user_id: uuid.UUID) -> UserInfoResponse:
        user = self._user_repo.find_by_id(user_id)
        if user is None:
            return UserInfoResponse(
                id=uuid.UUID(int=0), name="", email="", is_admin=False, is_active=False,
                created_at=datetime.min, last_login=datetime.min,
                error="User not found",
            )
        return UserInfoResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            is_admin=user.is_admin,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login,
        )
