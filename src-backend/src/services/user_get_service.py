# ruff: noqa: RUF002
"""获取当前用户信息服务。"""

from datetime import datetime

from pydantic import BaseModel
from src.services.interfaces.user_repository import UserRepository


class UserInfoResponse(BaseModel):
    """用户信息响应（不含密码）。"""

    id: int
    name: str
    email: str
    is_admin: bool
    is_active: bool
    roles: list[str]
    created_at: datetime
    last_login: datetime
    error: str | None = None


def _roles_from_admin_flag(is_admin: bool) -> list[str]:
    """根据 is_admin 字段映射前端角色列表。"""
    return ["R_ADMIN"] if is_admin else ["R_USER"]


class UserGetService:
    """获取当前用户信息用例。"""

    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    def execute(self, user_id: int) -> UserInfoResponse:
        user = self._user_repo.find_by_id(user_id)
        if user is None:
            return UserInfoResponse(
                id=0,
                name="",
                email="",
                is_admin=False,
                is_active=False,
                roles=[],
                created_at=datetime.min,
                last_login=datetime.min,
                error="User not found",
            )
        return UserInfoResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            is_admin=user.is_admin,
            is_active=user.is_active,
            roles=_roles_from_admin_flag(user.is_admin),
            created_at=user.created_at,
            last_login=user.last_login,
        )
