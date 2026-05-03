"""更新用户信息服务。"""
from typing import Optional

from pydantic import BaseModel

from src.services.interfaces.user_repository import UserRepository


class UserUpdateRequest(BaseModel):
    """更新用户请求 —— user_id 由路由层从 token 注入，不由客户端传入。"""
    name: Optional[str] = None
    email: Optional[str] = None
    old_password: Optional[str] = None   # 原密码，修改密码时必填
    password: Optional[str] = None       # 新密码


class UserUpdateResponse(BaseModel):
    success: bool = False
    error: Optional[str] = None


class UserUpdateService:
    """更新用户信息用例。"""

    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    def execute(self, user_id: int, request: UserUpdateRequest) -> UserUpdateResponse:
        user = self._user_repo.find_by_id(user_id)
        if user is None:
            return UserUpdateResponse(error="User not found.")

        if request.name:
            user.name = request.name
        if request.email:
            if self._user_repo.find_by_email(request.email):
                return UserUpdateResponse(error="Email already used.")
            user.email = request.email
        if request.old_password and request.password:
            from src.core.password_encryptor import verify_password, hash_password
            if not verify_password(request.old_password, user.password):
                return UserUpdateResponse(error="Old password is incorrect.")
            user.password = hash_password(request.password)

        self._user_repo.update(user.id, user)
        return UserUpdateResponse(success=True)
