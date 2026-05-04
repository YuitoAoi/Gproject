from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from src.app.dependencies import get_current_user, get_services
from src.services import ServiceFactory
from src.services.dataset_tag_service import (
    DatasetTagCreateRequest,
    DatasetTagCreateResponse,
    DatasetTagDeleteResponse,
    DatasetTagInfoGetResponse,
    DatasetTagsGetResponse,
    DatasetTagUpdateRequest,
    DatasetTagUpdateResponse,
)
from src.services.jwt_service import TokenPayload

router = APIRouter(prefix="/tag", tags=["tag"])
tags_router = APIRouter(tags=["tag"])


# ══════════════════════════════════════════════════════════
# GET /tags — 获取用户全部标签
# ══════════════════════════════════════════════════════════

@tags_router.get("/tags", response_model=DatasetTagsGetResponse)
def list_tags(
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    owner_id = int(current_user.user_id)
    return svc.dataset_tag().get_tags(owner_id)


# ══════════════════════════════════════════════════════════
# GET /tag/{tag_id} — 获取单个标签
# ══════════════════════════════════════════════════════════

@router.get("/{tag_id}", response_model=DatasetTagInfoGetResponse)
def get_tag(
    tag_id: int,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    owner_id = int(current_user.user_id)
    return svc.dataset_tag().get_tag(owner_id, tag_id)


# ══════════════════════════════════════════════════════════
# POST /tag — 创建标签
# ══════════════════════════════════════════════════════════

@router.post("/", response_model=DatasetTagCreateResponse, status_code=201)
def create_tag(
    request: DatasetTagCreateRequest,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    owner_id = int(current_user.user_id)
    result = svc.dataset_tag().create_tag(request, owner_id)
    if not result.success:
        return JSONResponse(content=result.model_dump(), status_code=400)
    return result


# ══════════════════════════════════════════════════════════
# PATCH /tag/{tag_id} — 更新标签
# ══════════════════════════════════════════════════════════

@router.patch("/{tag_id}", response_model=DatasetTagUpdateResponse)
def update_tag(
    tag_id: int,
    request: DatasetTagUpdateRequest,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    owner_id = int(current_user.user_id)
    request.tag_id = tag_id
    result = svc.dataset_tag().update_tag(request, owner_id)
    if not result.success:
        return JSONResponse(content=result.model_dump(), status_code=400)
    return result


# ══════════════════════════════════════════════════════════
# DELETE /tag/{tag_id} — 删除标签
# ══════════════════════════════════════════════════════════

@router.delete("/{tag_id}", response_model=DatasetTagDeleteResponse)
def delete_tag(
    tag_id: int,
    force: bool = Query(default=False, description="强制删除，同时移除关联数据集中的 tag"),
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    owner_id = int(current_user.user_id)
    result = svc.dataset_tag().delete_tag(owner_id, tag_id, force=force)
    if not result.success:
        return JSONResponse(content=result.model_dump(), status_code=400)
    return result
