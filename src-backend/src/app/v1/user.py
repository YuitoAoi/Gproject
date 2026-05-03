from fastapi import APIRouter, Depends

from src.app.dependencies import get_current_user, get_services
from src.services import (
    ServiceFactory,
    UserLoginRequest,
    UserLoginResponse,
    UserInfoResponse,
    UserUpdateRequest,
    UserUpdateResponse,
    UserRegisterRequest,
    UserRegisterResponse,

)
from src.services.jwt_service import TokenPayload

auth_api = APIRouter(
    prefix='/auth'
)

@auth_api.post("/login", response_model = UserLoginResponse)
def login_user(
    request: UserLoginRequest,
    svc: ServiceFactory = Depends(get_services),
):
    return svc.login_user().execute(request)


user_api = APIRouter(
    prefix="/user"
)


@user_api.get("", response_model = UserInfoResponse)
def get_current_user_info(
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    """获取当前用户信息（不含密码）。"""
    return svc.get_user_info().execute(int(current_user.user_id))

@user_api.patch("", response_model=UserUpdateResponse)
def update_user_info(
    request: UserUpdateRequest,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    """更新当前用户信息（需 Bearer token）。"""
    return svc.update_user_info().execute(int(current_user.user_id), request)

@user_api.post("", response_model = UserRegisterResponse, status_code=201)
def register_user(
    request: UserRegisterRequest,
    svc: ServiceFactory = Depends(get_services),
):
    from fastapi.responses import JSONResponse

    result = svc.register_user().execute(request)
    if not result.success:
        return JSONResponse(
            content=result.model_dump(),
            status_code=400,
        )
    return result
