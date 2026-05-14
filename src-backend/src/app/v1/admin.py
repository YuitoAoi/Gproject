# ruff: noqa: RUF002
"""管理员用户管理 API。"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from src.app.dependencies import get_current_user, get_services
from src.services import ServiceFactory
from src.services.jwt_service import TokenPayload
from src.services.user_manage_service import (
    AdminResetPasswordRequest,
    AdminSetAdminRequest,
    AdminToggleActiveRequest,
    AdminUserListResponse,
    AdminOperationResponse,
)

logger = logging.getLogger(__name__)

admin_api = APIRouter(prefix="/admin", tags=["admin"])


def get_admin_user(
    request: Request,
    current_user: TokenPayload = Depends(get_current_user),
) -> TokenPayload:
    """校验当前用户为管理员，否则 403。"""
    svc: ServiceFactory = request.app.state.services
    user = svc.user_repo.find_by_id(int(current_user.user_id))
    if user is None or not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    return current_user


@admin_api.get("/users", response_model=AdminUserListResponse)
def admin_list_users(
    page: int = 1,
    size: int = 10,
    keyword: str | None = None,
    svc: ServiceFactory = Depends(get_services),
    _admin: TokenPayload = Depends(get_admin_user),
):
    """管理员获取用户列表（分页+搜索）。"""
    return svc.manage_users().list_users(page, size, keyword)


@admin_api.patch("/users/{user_id}/active", response_model=AdminOperationResponse)
def admin_toggle_user_active(
    user_id: int,
    request: AdminToggleActiveRequest,
    svc: ServiceFactory = Depends(get_services),
    _admin: TokenPayload = Depends(get_admin_user),
):
    """管理员启用/禁用用户。"""
    result = svc.manage_users().toggle_active(user_id, request)
    if not result.success:
        return JSONResponse(content=result.model_dump(), status_code=400)
    return result


@admin_api.patch("/users/{user_id}/admin", response_model=AdminOperationResponse)
def admin_set_user_admin(
    user_id: int,
    request: AdminSetAdminRequest,
    svc: ServiceFactory = Depends(get_services),
    _admin: TokenPayload = Depends(get_admin_user),
):
    """管理员设置/取消用户管理员角色。"""
    result = svc.manage_users().set_admin(user_id, request)
    if not result.success:
        return JSONResponse(content=result.model_dump(), status_code=400)
    return result


@admin_api.post("/users/{user_id}/reset-password", response_model=AdminOperationResponse)
def admin_reset_password(
    user_id: int,
    request: AdminResetPasswordRequest,
    svc: ServiceFactory = Depends(get_services),
    _admin: TokenPayload = Depends(get_admin_user),
):
    """管理员重置用户密码。"""
    result = svc.manage_users().reset_password(user_id, request)
    if not result.success:
        return JSONResponse(content=result.model_dump(), status_code=400)
    return result


@admin_api.delete("/users/{user_id}", response_model=AdminOperationResponse)
def admin_delete_user(
    user_id: int,
    svc: ServiceFactory = Depends(get_services),
    _admin: TokenPayload = Depends(get_admin_user),
):
    """管理员删除用户。"""
    result = svc.manage_users().delete_user(user_id)
    if not result.success:
        return JSONResponse(content=result.model_dump(), status_code=400)
    return result
