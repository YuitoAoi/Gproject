# ruff: noqa: RUF002, RUF003
"""JWT 认证服务"""

import os
import time
from dataclasses import dataclass

import jwt


@dataclass
class TokenPayload:
    """Token 载荷"""

    user_id: str
    email: str = ""
    exp: int = 0


@dataclass
class TokenPair:
    """Token 对"""

    access_token: str
    refresh_token: str
    expires_in: int  # access_token 有效期（秒）


class JWTService:
    """JWT 服务 - 生成和验证 Token"""

    def __init__(
        self,
        secret_key: str | None = None,
        access_token_expire: int = 3600,  # 1小时
        refresh_token_expire: int = 604800,  # 7天
    ):
        self._secret_key = secret_key or os.environ.get("JWT_SECRET_KEY", "your-super-secret-key-change-in-production")
        self._algorithm = "HS256"
        self._access_token_expire = access_token_expire
        self._refresh_token_expire = refresh_token_expire

    def generate_token_pair(self, user_id: str, email: str = "") -> TokenPair:
        """生成 Token 对（access_token + refresh_token）"""
        now = int(time.time())

        access_payload = {
            "sub": user_id,
            "email": email,
            "type": "access",
            "iat": now,
            "exp": now + self._access_token_expire,
        }
        access_token = jwt.encode(access_payload, self._secret_key, algorithm=self._algorithm)

        refresh_payload = {
            "sub": user_id,
            "email": email,
            "type": "refresh",
            "iat": now,
            "exp": now + self._refresh_token_expire,
        }
        refresh_token = jwt.encode(refresh_payload, self._secret_key, algorithm=self._algorithm)

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self._access_token_expire,
        )

    def verify_access_token(self, token: str) -> TokenPayload | None:
        """验证 Access Token"""
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
            if payload.get("type") != "access":
                return None
            return TokenPayload(
                user_id=payload.get("sub", ""),
                email=payload.get("email", ""),
                exp=payload.get("exp", 0),
            )
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def verify_refresh_token(self, token: str) -> str | None:
        """验证 Refresh Token，返回 user_id"""
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
            if payload.get("type") != "refresh":
                return None
            return payload["sub"]
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def refresh_access_token(self, refresh_token: str) -> TokenPair | None:
        """使用 Refresh Token 刷新 Access Token"""
        user_id = self.verify_refresh_token(refresh_token)
        if not user_id:
            return None
        return self.generate_token_pair(user_id)

    # ── 下载令牌 ──────────────────────────────────────────────

    def generate_download_token(self, *, dataset_id: int, user_id: int, expire_seconds: int = 900) -> str:
        """生成短时效下载令牌（默认 15 分钟）。"""
        now = int(time.time())
        payload = {
            "sub": str(user_id),
            "dataset_id": dataset_id,
            "type": "download",
            "iat": now,
            "exp": now + expire_seconds,
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def verify_download_token(self, token: str) -> dict | None:
        """验证下载令牌，返回 {user_id, dataset_id} 或 None。"""
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
            if payload.get("type") != "download":
                return None
            return {
                "user_id": int(payload["sub"]),
                "dataset_id": payload["dataset_id"],
            }
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, KeyError):
            return None
