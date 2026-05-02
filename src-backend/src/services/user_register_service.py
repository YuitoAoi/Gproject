import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from src.core.user import User
from src.core.password_encryptor import hash_password
from src.services.interfaces.user_repository import UserRepository


class UserRegisterRequest(BaseModel):
    """注册请求"""
    name: str
    email: str
    password: str


class UserRegisterResponse(BaseModel):
    """注册响应"""
    user_id: Optional[int] = None
    name: Optional[str] = None
    email: Optional[str] = None
    success: bool = False
    error: Optional[str] = None


class UserRegisterService:
    """用户注册用例。"""

    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    def execute(self, request: UserRegisterRequest) -> UserRegisterResponse:
        # 校验用户名
        if not request.name or not request.name.strip():
            return UserRegisterResponse(error="Invalid name.")

        # 校验邮箱
        if not _is_valid_email(request.email):
            return UserRegisterResponse(error="Invalid email.")

        # 校验密码强度
        if not _is_strong_password(request.password):
            return UserRegisterResponse(
                error="Password must be at least 8 characters "
                      "with 2 of: uppercase, lowercase, digit, special char."
            )

        # 检查邮箱是否已被注册
        if self._user_repo.find_by_email(request.email):
            return UserRegisterResponse(error="Email already used.")

        # 创建用户实体
        now = datetime.now()
        user = User(
            id=0,
            name=request.name,
            email=request.email,
            password=hash_password(request.password),
            is_admin=False,
            is_active=True,
            created_at=now,
            last_login=now,
        )

        new_id = self._user_repo.create(user)
        if new_id is None:
            return UserRegisterResponse(
                error="Failed to create user."
            )

        return UserRegisterResponse(
            user_id=new_id,
            name=user.name,
            email=user.email,
            success=True,
        )


# ── 校验工具 ──────────────────────────────────────────────


def _is_valid_email(email: str) -> bool:
    """基础邮箱格式校验。"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def _is_strong_password(password: str) -> bool:
    """密码强度：>=8 位，至少包含大小写/数字/特殊字符中的 2 类。"""
    if len(password) < 8:
        return False
    count = 0
    if re.search(r'[a-z]', password):
        count += 1
    if re.search(r'[A-Z]', password):
        count += 1
    if re.search(r'\d', password):
        count += 1
    if re.search(r'[^a-zA-Z0-9]', password):
        count += 1
    return count >= 2
