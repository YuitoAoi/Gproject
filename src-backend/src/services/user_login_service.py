import logging
import uuid
from datetime import datetime

from pydantic import BaseModel

_logger = logging.getLogger(__name__)

from src.core.password_encryptor import verify_password
from src.services.interfaces.user_repository import UserRepository
from src.services.jwt_service import JWTService
from src.services.utils import is_valid_email


class UserLoginRequest(BaseModel):
    """登录请求。仅接受 email + password。"""
    email: str
    password: str


class UserLoginResponse(BaseModel):
    """登录响应"""
    user_id: uuid.UUID | None = None
    access_token: str | None = None
    refresh_token: str | None = None
    expires_in: int | None = None
    success: bool = False
    error: str | None = None


class UserLoginService:
    """用户登录用例 - 同步版本"""

    def __init__(
        self,
        jwt_service: JWTService,
        user_repo: UserRepository,
    ):
        self._jwt_service = jwt_service
        self._user_repo = user_repo

    def execute(
        self, request: UserLoginRequest, login_ip: str = ""
    ) -> UserLoginResponse:
        if not request.email:
            return UserLoginResponse(error="Email cannot be empty.")
        if not request.password:
            return UserLoginResponse(error="Password cannot be empty.")
        if not is_valid_email(request.email):
            return UserLoginResponse(error="Invalid email format.")

        user = self._user_repo.find_by_email(request.email)
        if not user:
            return UserLoginResponse(error="User not found.")

        if not verify_password(request.password, user.password):
            return UserLoginResponse(error="Wrong password.")

        user.last_login = datetime.now()
        user.last_login_ip = login_ip
        try:
            self._user_repo.update(user.id, user)
        except Exception:
            _logger.exception("Failed to update last_login for user_id=%s", user.id)

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