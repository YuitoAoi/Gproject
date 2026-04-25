from fastapi import APIRouter

router = APIRouter()


@router.get('/info')
async def get_user_info():
    """获取当前用户信息（开发模式返回模拟数据）"""
    return {
        'userId': 1,
        'userName': 'admin',
        'email': 'admin@local.dev',
        'roles': ['R_SUPER'],
        'buttons': ['*'],
        'avatar': ''
    }
