from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from src.app.dependencies import get_current_user, get_services
from src.services import (
    ServiceFactory,
    UserInfoResponse,
    UserLoginRequest,
    UserLoginResponse,
    UserRegisterRequest,
    UserRegisterResponse,
    UserUpdateRequest,
    UserUpdateResponse,
)
from src.services.jwt_service import TokenPayload


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class TokenRefreshResponse(BaseModel):
    access_token: str | None = None
    refresh_token: str | None = None
    expires_in: int | None = None
    success: bool = False
    error: str | None = None


auth_api = APIRouter(prefix="/auth")
user_api = APIRouter(prefix="/user")


@auth_api.post("/login", response_model=UserLoginResponse)
def login_user(
    req_body: UserLoginRequest,
    req: Request,
    svc: ServiceFactory = Depends(get_services),
):
    from src.app.middleware.rate_limiter import login_limiter

    client_ip = req.client.host if req.client else ""
    if not login_limiter.is_allowed(client_ip):
        return JSONResponse(
            content={"success": False, "error": "Too many requests. Please try again later."},
            status_code=429,
        )
    result = svc.login_user().execute(req_body, login_ip=client_ip)
    if not result.success:
        err = result.error or ""
        status = 400 if ("empty" in err or "Invalid" in err) else 401
        return JSONResponse(content=result.model_dump(mode="json"), status_code=status)
    return result


@user_api.get("", response_model=UserInfoResponse)
def get_current_user_info(
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    result = svc.get_user_info().execute(int(current_user.user_id))
    if result.error:
        return JSONResponse(content=result.model_dump(mode="json"), status_code=404)
    return result


@user_api.patch("", response_model=UserUpdateResponse)
def update_user_info(
    request: UserUpdateRequest,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    result = svc.update_user_info().execute(int(current_user.user_id), request)
    if not result.success:
        err = result.error or ""
        status = 409 if "already" in err.lower() else 400
        return JSONResponse(content=result.model_dump(mode="json"), status_code=status)
    return result


@auth_api.post("/refresh", response_model=TokenRefreshResponse)
def refresh_token(
    request: TokenRefreshRequest,
    svc: ServiceFactory = Depends(get_services),
):
    token_pair = svc.jwt().refresh_access_token(request.refresh_token)
    if token_pair is None:
        return JSONResponse(
            content={"success": False, "error": "Invalid or expired refresh token"},
            status_code=401,
        )
    return TokenRefreshResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
        expires_in=token_pair.expires_in,
        success=True,
    )


@user_api.post("", response_model=UserRegisterResponse, status_code=201)
def register_user(
    req_body: UserRegisterRequest,
    req: Request,
    svc: ServiceFactory = Depends(get_services),
):
    from src.app.middleware.rate_limiter import register_limiter

    client_ip = req.client.host if req.client else ""
    if not register_limiter.is_allowed(client_ip):
        return JSONResponse(
            content={"success": False, "error": "Too many requests. Please try again later."},
            status_code=429,
        )
    result = svc.register_user().execute(req_body)
    if not result.success:
        err = result.error or ""
        status = 409 if "already" in err.lower() else 400
        return JSONResponse(content=result.model_dump(mode="json"), status_code=status)
    return result
