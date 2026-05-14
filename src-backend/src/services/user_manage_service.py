# ruff: noqa: RUF002
"""管理员用户管理服务：列表分页、启用/禁用、设置管理员角色、重置密码、删除。"""

from datetime import datetime

from pydantic import BaseModel
from src.core.password_encryptor import hash_password
from src.services.interfaces.user_repository import UserRepository


class AdminUserListItem(BaseModel):
    """管理员视角的用户列表项。"""

    id: int
    name: str
    email: str
    is_admin: bool
    is_active: bool
    roles: list[str]
    created_at: datetime
    last_login: datetime


class AdminUserListResponse(BaseModel):
    """分页用户列表响应。"""

    records: list[AdminUserListItem]
    current: int
    size: int
    total: int


class AdminToggleActiveRequest(BaseModel):
    is_active: bool


class AdminSetAdminRequest(BaseModel):
    is_admin: bool


class AdminResetPasswordRequest(BaseModel):
    new_password: str


class AdminOperationResponse(BaseModel):
    success: bool = False
    error: str | None = None


def _roles_from_admin_flag(is_admin: bool) -> list[str]:
    return ["R_ADMIN"] if is_admin else ["R_USER"]


class UserManageService:
    """管理员用户管理服务。"""

    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    def list_users(self, page: int, size: int, keyword: str | None = None) -> AdminUserListResponse:
        """分页查询用户列表。"""
        result = self._user_repo.find_all_paginated(page, size, keyword)
        records = [
            AdminUserListItem(
                id=u.id,
                name=u.name,
                email=u.email,
                is_admin=u.is_admin,
                is_active=u.is_active,
                roles=_roles_from_admin_flag(u.is_admin),
                created_at=u.created_at,
                last_login=u.last_login,
            )
            for u in result.records
        ]
        return AdminUserListResponse(
            records=records,
            current=result.current,
            size=result.size,
            total=result.total,
        )

    def toggle_active(self, user_id: int, request: AdminToggleActiveRequest) -> AdminOperationResponse:
        """启用/禁用用户。"""
        user = self._user_repo.find_by_id(user_id)
        if user is None:
            return AdminOperationResponse(error="用户不存在")
        if user_id == 0:
            return AdminOperationResponse(error="无法修改超级管理员状态")
        user.is_active = request.is_active
        self._user_repo.update(user_id, user)
        return AdminOperationResponse(success=True)

    def set_admin(self, user_id: int, request: AdminSetAdminRequest) -> AdminOperationResponse:
        """设置/取消管理员角色。"""
        user = self._user_repo.find_by_id(user_id)
        if user is None:
            return AdminOperationResponse(error="用户不存在")
        if user_id == 0:
            return AdminOperationResponse(error="无法修改超级管理员角色")
        user.is_admin = request.is_admin
        self._user_repo.update(user_id, user)
        return AdminOperationResponse(success=True)

    def reset_password(self, user_id: int, request: AdminResetPasswordRequest) -> AdminOperationResponse:
        """重置用户密码。"""
        user = self._user_repo.find_by_id(user_id)
        if user is None:
            return AdminOperationResponse(error="用户不存在")
        if user_id == 0:
            return AdminOperationResponse(error="无法重置超级管理员密码")
        user.password = hash_password(request.new_password)
        self._user_repo.update(user_id, user)
        return AdminOperationResponse(success=True)

    def delete_user(self, user_id: int) -> AdminOperationResponse:
        """删除用户。"""
        if user_id == 0:
            return AdminOperationResponse(error="无法删除超级管理员")
        user = self._user_repo.find_by_id(user_id)
        if user is None:
            return AdminOperationResponse(error="用户不存在")
        self._user_repo.remove(user_id)
        return AdminOperationResponse(success=True)
