from datetime import datetime
from pydantic import BaseModel



class User(BaseModel):
    id:int
    name: str
    email: str
    password: str   # 加密后密码，禁止明文存储，DTO字段时转换为******隐藏
    is_admin: bool
    is_active: bool
    created_at: datetime
    last_login: datetime