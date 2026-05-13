from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from src.app.dependencies import get_current_user, get_services
from src.services import ServiceFactory
from src.services.dataset_tag_service import (
    DatasetTagCreateRequest,
    DatasetTagCreateResponse,
    DatasetTagDeleteRequest,
    DatasetTagDeleteResponse,
    DatasetTagInfoGetRequest,
    DatasetTagInfoGetResponse,
    DatasetTagsGetResponse,
    DatasetTagUpdateRequest,
    DatasetTagUpdateResponse,
)
from src.services.jwt_service import TokenPayload

router = APIRouter(prefix="/tag", tags=["tag"])
tags_router = APIRouter(tags=["tag"])


# ══════════════════════════════════════════════════════════
# GET /tags
# ══════════════════════════════════════════════════════════


@tags_router.get("/tags", response_model=DatasetTagsGetResponse)
def list_tags(
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    owner_id = int(current_user.user_id)
    return svc.dataset_tag().get_tags(owner_id)


# ══════════════════════════════════════════════════════════
# POST /tag/get
# ══════════════════════════════════════════════════════════


@router.post("/get", response_model=DatasetTagInfoGetResponse)
def get_tag(
    request: DatasetTagInfoGetRequest,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    owner_id = int(current_user.user_id)
    result = svc.dataset_tag().get_tag(owner_id, request.tag_id)
    if not result.success:
        return JSONResponse(content=result.model_dump(mode="json"), status_code=404)
    return result


# ══════════════════════════════════════════════════════════
# POST /tag
# ══════════════════════════════════════════════════════════


@router.post("", response_model=DatasetTagCreateResponse, status_code=201)
def create_tag(
    request: DatasetTagCreateRequest,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    owner_id = int(current_user.user_id)
    result = svc.dataset_tag().create_tag(request, owner_id)
    if not result.success:
        return JSONResponse(content=result.model_dump(mode="json"), status_code=400)
    return result


# ══════════════════════════════════════════════════════════
# PATCH /tag
# ══════════════════════════════════════════════════════════


@router.patch("", response_model=DatasetTagUpdateResponse)
def update_tag(
    request: DatasetTagUpdateRequest,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    owner_id = int(current_user.user_id)
    result = svc.dataset_tag().update_tag(request, owner_id)
    if not result.success:
        return JSONResponse(content=result.model_dump(mode="json"), status_code=404)
    return result


# ══════════════════════════════════════════════════════════
# DELETE /tag
# ══════════════════════════════════════════════════════════


@router.delete("", response_model=DatasetTagDeleteResponse)
def delete_tag(
    request: DatasetTagDeleteRequest,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    owner_id = int(current_user.user_id)
    result = svc.dataset_tag().delete_tag(owner_id, request.tag_id, force=request.force)
    if not result.success:
        return JSONResponse(content=result.model_dump(mode="json"), status_code=400)
    return result
