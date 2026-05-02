from typing import Optional
from datetime import datetime

from pydantic import BaseModel

from src.services.interfaces.user_repository import UserRepository
from src.services.jwt_service import JWTService


class UserLoginRequest(BaseModel):
    """登录请求"""
    email: str
    password: str
    login_ip: Optional[str] = None


class UserLoginResponse(BaseModel):
    """登录响应"""
    user_id: Optional[int] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    success: bool = False
    error: Optional[str] = None


class UserLoginService:
    """用户登录用例 - 同步版本"""

    def __init__(
        self,
        jwt_service: JWTService,
        user_repo: UserRepository,
    ):
        self._jwt_service = jwt_service
        self._user_repo = user_repo

    def execute(self, request: UserLoginRequest) -> UserLoginResponse:
        if not request.email:
            return UserLoginResponse(
                error=f"{ValueError('Email cannot be none.')}"
            )
        if not request.password:
            return UserLoginResponse(
                error=f"{ValueError('Auth password cannot be none.')}"
            )

        user = self._user_repo.find_by_email(request.email)
        if not user:
            return UserLoginResponse(
                error=f"{ValueError('User not found')}"
            )

        from src.core.password_encryptor import verify_password
        if not verify_password(request.password, user.password):
            return UserLoginResponse(
                error=f"{ValueError('Wrong password.')}"
            )

        # 更新最后登录时间
        user.last_login = datetime.now()
        self._user_repo.update(user.id, user)

        # 生成 JWT Token
        token_pair = self._jwt_service.generate_token_pair(
            user_id=str(user.id), email=user.email
        )

        return UserLoginResponse(
            user_id=user.id,
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
            expires_in=token_pair.expires_in,
            success=True,
        )