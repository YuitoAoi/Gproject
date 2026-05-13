# ruff: noqa: RUF003
from datetime import datetime

from pydantic import BaseModel
from src.core.password_encryptor import hash_password
from src.core.user import User
from src.services.interfaces.user_repository import UserRepository
from src.services.utils import is_safe_name, is_safe_password, is_strong_password, is_valid_email


class UserRegisterRequest(BaseModel):
    """注册请求"""

    name: str
    email: str
    password: str


class UserRegisterResponse(BaseModel):
    """注册响应"""

    user_id: int | None = None
    name: str | None = None
    email: str | None = None
    success: bool = False
    error: str | None = None


class UserRegisterService:
    """用户注册用例。"""

    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    def execute(self, request: UserRegisterRequest) -> UserRegisterResponse:
        # 校验用户名
        if not is_safe_name(request.name):
            return UserRegisterResponse(error="Invalid name.")

        # 校验邮箱（标准化处理）
        request.email = request.email.strip().lower()
        if not is_valid_email(request.email):
            return UserRegisterResponse(error="Invalid email.")

        # 校验密码
        if not is_safe_password(request.password):
            return UserRegisterResponse(error="Password contains invalid characters.")
        if not is_strong_password(request.password):
            return UserRegisterResponse(
                error="Password must be at least 8 characters with 2 of: uppercase, lowercase, digit, special char."
            )

        # 检查邮箱是否已被注册（大小写不敏感）
        existing = self._user_repo.find_by_email(request.email)
        if existing is not None:
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
            return UserRegisterResponse(error="Failed to create user.")

        return UserRegisterResponse(
            user_id=new_id,
            name=user.name,
            email=user.email,
            success=True,
        )
