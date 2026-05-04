from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

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

auth_api = APIRouter(prefix="/auth")
user_api = APIRouter(prefix="/user")


@auth_api.post("/login", response_model=UserLoginResponse)
def login_user(
    request: UserLoginRequest,
    svc: ServiceFactory = Depends(get_services),
):
    result = svc.login_user().execute(request)
    if not result.success:
        return JSONResponse(content=result.model_dump(), status_code=401)
    return result


@user_api.get("", response_model=UserInfoResponse)
def get_current_user_info(
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    result = svc.get_user_info().execute(int(current_user.user_id))
    if result.error:
        return JSONResponse(content=result.model_dump(), status_code=404)
    return result


@user_api.patch("", response_model=UserUpdateResponse)
def update_user_info(
    request: UserUpdateRequest,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    result = svc.update_user_info().execute(int(current_user.user_id), request)
    if not result.success:
        return JSONResponse(content=result.model_dump(), status_code=400)
    return result


@user_api.post("", response_model=UserRegisterResponse, status_code=201)
def register_user(
    request: UserRegisterRequest,
    svc: ServiceFactory = Depends(get_services),
):
    result = svc.register_user().execute(request)
    if not result.success:
        return JSONResponse(content=result.model_dump(), status_code=400)
    return result
