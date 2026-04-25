from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json

router = APIRouter()


class LoginRequest(BaseModel):
    userName: str
    password: str


@router.post('/login')
async def login(request: LoginRequest):
    """用户登录接口（开发模式 mock）"""
    print(f"[Auth] 收到登录请求: userName={request.userName}")
    if request.userName == 'admin' and request.password == 'admin123':
        response_data = {
            'code': 200,
            'msg': '登录成功',
            'data': {
                'userId': 1,
                'userName': 'admin',
                'token': 'mock-token-for-dev',
                'refreshToken': 'mock-refresh-token-for-dev'
            }
        }
        print(f"[Auth] 返回数据: {json.dumps(response_data, ensure_ascii=False)}")
        return response_data
    print(f"[Auth] 登录失败: {request.userName}")
    raise HTTPException(status_code=401, detail='用户名或密码错误')