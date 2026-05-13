# ruff: noqa: RUF002
"""FastAPI 依赖注入：服务工厂、认证与授权。"""

from fastapi import Header, HTTPException, Request, status
from src.services import ServiceFactory
from src.services.jwt_service import TokenPayload


def get_services(request: Request) -> ServiceFactory:
    """从 app.state 获取 ServiceFactory，供路由 Depends 使用。"""
    return request.app.state.services


def get_current_user(
    request: Request,
    authorization: str | None = Header(None),
) -> TokenPayload:
    """从 Authorization 头提取并验证 Bearer token，返回 TokenPayload。

    用法::

        @router.get("/protected")
        def protected_route(current_user = Depends(get_current_user)):
            print(current_user.user_id)   # 当前用户 ID
            ...

    无有效 token 时直接返回 401，不执行路由逻辑。
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header.",
        )

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected: Bearer <token>",
        )

    svc = request.app.state.services
    payload = svc.jwt().verify_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
        )

    return payload
