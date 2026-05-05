from datetime import datetime
import uuid
from pydantic import field_serializer
from .entity_base import EntityBase


class User(EntityBase):
    id: uuid.UUID
    name: str
    email: str
    password: str  # 加密后密码，禁止明文存储，DTO字段时转换为******隐藏
    is_admin: bool
    is_active: bool
    created_at: datetime
    last_login: datetime
    last_login_ip: str = ""

    @field_serializer("password")
    def serialize_password(self, v: str) -> str:
        return "******"
