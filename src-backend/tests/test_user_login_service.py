# ruff: noqa: E402
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

_SERVICES_DIR = Path(__file__).resolve().parent.parent / "src" / "services"
if str(_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(_SERVICES_DIR))

from src.core.user import User
from src.services.jwt_service import TokenPair
from src.services.user_login_service import (
    UserLoginRequest,
    UserLoginService,
)


def _make_user(name="testuser", email="test@example.com", password="hashed_password") -> User:
    now = datetime.now()
    return User(
        id=1,
        name=name,
        email=email,
        password=password,
        is_admin=False,
        is_active=True,
        created_at=now,
        last_login=now,
        last_login_ip="",
    )


def _make_token_pair() -> TokenPair:
    return TokenPair(
        access_token="access-token-mock",
        refresh_token="refresh-token-mock",
        expires_in=3600,
    )


class TestUserLoginService:
    """UserLoginService.execute() 单元测试"""

    def test_login_success(self):
        """正确的邮箱和密码 → success=True + token"""
        user = _make_user()
        token_pair = _make_token_pair()

        mock_repo = MagicMock()
        mock_repo.find_by_email.return_value = user

        mock_jwt = MagicMock()
        mock_jwt.generate_token_pair.return_value = token_pair

        with patch("src.services.user_login_service.verify_password", return_value=True):
            service = UserLoginService(
                jwt_service=mock_jwt,
                user_repo=mock_repo,
            )
            result = service.execute(UserLoginRequest(email=user.email, password="correct"))

        assert result.success is True
        assert result.user_id == user.id
        assert result.access_token == "access-token-mock"
        assert result.refresh_token == "refresh-token-mock"
        assert result.expires_in == 3600
        assert result.error is None

    def test_login_email_empty(self):
        """邮箱为空 → error"""
        mock_repo = MagicMock()
        mock_jwt = MagicMock()

        service = UserLoginService(
            jwt_service=mock_jwt,
            user_repo=mock_repo,
        )
        result = service.execute(UserLoginRequest(email="", password="secret"))

        assert result.success is False
        assert "Email cannot be empty" in result.error
        mock_jwt.generate_token_pair.assert_not_called()
        mock_repo.find_by_email.assert_not_called()

    def test_login_password_empty(self):
        """密码为空 → error"""
        mock_repo = MagicMock()
        mock_jwt = MagicMock()

        service = UserLoginService(
            jwt_service=mock_jwt,
            user_repo=mock_repo,
        )
        result = service.execute(UserLoginRequest(email="test@x.com", password=""))

        assert result.success is False
        assert "Password cannot be empty" in result.error

    def test_login_user_not_found(self):
        """用户不存在 → User not found"""
        mock_repo = MagicMock()
        mock_repo.find_by_email.return_value = None
        mock_jwt = MagicMock()

        service = UserLoginService(
            jwt_service=mock_jwt,
            user_repo=mock_repo,
        )
        result = service.execute(UserLoginRequest(email="ghost@x.com", password="any"))

        assert result.success is False
        assert "User not found" in result.error

    def test_login_wrong_password(self):
        """密码错误 → Wrong password"""
        user = _make_user(password="correct_hash")
        mock_repo = MagicMock()
        mock_repo.find_by_email.return_value = user
        mock_jwt = MagicMock()

        with patch("src.services.user_login_service.verify_password", return_value=False):
            service = UserLoginService(
                jwt_service=mock_jwt,
                user_repo=mock_repo,
            )
            result = service.execute(UserLoginRequest(email=user.email, password="wrong"))

        assert result.success is False
        assert "Wrong password" in result.error

    def test_login_ip_optional(self):
        """不传 login_ip 也能正常登录"""
        user = _make_user()
        token_pair = _make_token_pair()

        mock_repo = MagicMock()
        mock_repo.find_by_email.return_value = user

        mock_jwt = MagicMock()
        mock_jwt.generate_token_pair.return_value = token_pair

        with patch("src.services.user_login_service.verify_password", return_value=True):
            service = UserLoginService(
                jwt_service=mock_jwt,
                user_repo=mock_repo,
            )
            request = UserLoginRequest(email=user.email, password="correct")
            result = service.execute(request)

        assert result.success is True
