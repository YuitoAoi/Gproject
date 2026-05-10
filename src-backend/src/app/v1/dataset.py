from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Request, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from src.app.dependencies import get_current_user, get_services
from src.services import (
    GetDatasetResponse,
    GetDatasetsResponse,
    GetTimesResponse,
    ServiceFactory,
)
from src.services.dataset_import_export_service import (
    CompleteUploadRequest,
    CompleteUploadResponse,
    DatasetDownloadRequest,
    DatasetDownloadTokenResponse,
    DatasetImportExportResponse,
    DatasetImportRequest,
    InitiateUploadRequest,
    InitiateUploadResponse,
    UploadChunkResponse,
    UploadStatusResponse,
)
from src.services.dataset_process_service import (
    DatasetProcessRequest,
    DatasetProcessResponse,
    SampleRequest,
    SampleResponse,
)
from src.services.dataset_remove_service import (
    DatasetRemoveRequest,
    DatasetRemoveResponse,
)
from src.services.dataset_update_service import (
    DatasetUpdateRequest,
    DatasetUpdateResponse,
    DatasetAddTagsBatchRequest,
    DatasetAddTagsBatchResponse,
)
from src.services.jwt_service import TokenPayload

router = APIRouter(prefix="/dataset", tags=["dataset"])
datasets_router = APIRouter(prefix="/datasets", tags=["dataset"])
download_router = APIRouter(tags=["download"])


def _check_owner(svc, dataset_id: int, owner_id: int) -> JSONResponse | None:
    ds = svc.dataset_repo.find_by_id(dataset_id)
    if ds is None:
        return JSONResponse(
            {"success": False, "error": f"Dataset not found: {dataset_id}"},
            status_code=404,
        )
    if ds.owner_id != owner_id:
        return JSONResponse(
            {"success": False, "error": f"Dataset not found: {dataset_id}"},
            status_code=404,
        )
    return None


# ══════════════════════════════════════════════════════════
# 查询
# ══════════════════════════════════════════════════════════


@datasets_router.get("", response_model=GetDatasetsResponse)
def list_datasets(
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    owner_id = int(current_user.user_id)
    return svc.get_datasets().get_all(owner_id=owner_id)


@datasets_router.get("/times", response_model=GetTimesResponse)
def get_dataset_times(
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    owner_id = int(current_user.user_id)
    return svc.get_datasets().get_times(owner_id=owner_id)


@router.post("/get", response_model=GetDatasetResponse)
def get_dataset(
    request: DatasetDownloadRequest,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    owner_id = int(current_user.user_id)
    result = svc.get_datasets().get_by_id(request.dataset_id, owner_id)
    if result.error:
        return JSONResponse(content=result.model_dump(mode='json'), status_code=404)
    return result


# ══════════════════════════════════════════════════════════
# 导入
# ══════════════════════════════════════════════════════════


@router.post("/import", response_model=DatasetImportExportResponse, status_code=201)
def import_dataset(
    request: DatasetImportRequest,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    owner_id = int(current_user.user_id)
    result = svc.dataset_import_export().import_dataset(request, owner_id)
    if not result.success:
        return JSONResponse(content=result.model_dump(mode='json'), status_code=400)
    return result


# ══════════════════════════════════════════════════════════
# 分块上传
# ══════════════════════════════════════════════════════════


@router.post("/upload/initiate", response_model=InitiateUploadResponse)
def initiate_upload(
    request: InitiateUploadRequest,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    return svc.chunked_upload().initiate(request)


@router.post("/upload/chunk", response_model=UploadChunkResponse)
def upload_chunk(
    upload_id: str = Form(...),
    chunk_index: int = Form(...),
    file: UploadFile = File(...),
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    data = file.file.read()
    result = svc.chunked_upload().upload_chunk(upload_id, chunk_index, data)
    if result.error:
        return JSONResponse(content=result.model_dump(mode='json'), status_code=400)
    return result


@router.post("/upload/status", response_model=UploadStatusResponse)
def upload_status(
    upload_id: str = Form(...),
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    return svc.chunked_upload().get_status(upload_id)


@router.post("/upload/complete", response_model=CompleteUploadResponse)
def complete_upload(
    request: CompleteUploadRequest,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    request.owner_id = int(current_user.user_id)
    result = svc.chunked_upload().complete(request)
    if not result.success:
        return JSONResponse(content=result.model_dump(mode='json'), status_code=400)
    return result


# ══════════════════════════════════════════════════════════
# 更新
# ══════════════════════════════════════════════════════════


@router.patch("", response_model=DatasetUpdateResponse)
def update_dataset(
    request: DatasetUpdateRequest,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    owner_id = int(current_user.user_id)
    result = svc.update_dataset().execute(request, owner_id)
    if not result.success:
        return JSONResponse(content=result.model_dump(mode='json'), status_code=404)
    return result


@datasets_router.patch("/tags", response_model=DatasetAddTagsBatchResponse)
def add_tags_batch(
    request: DatasetAddTagsBatchRequest,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    owner_id = int(current_user.user_id)
    result = svc.add_tags_batch().execute(request, owner_id)
    if not result.success:
        return JSONResponse(content=result.model_dump(mode='json'), status_code=400)
    return result


# ══════════════════════════════════════════════════════════
# 样本 & 处理
# ══════════════════════════════════════════════════════════


@router.post("/sample", response_model=SampleResponse)
def get_dataset_sample(
    request: SampleRequest,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    owner_id = int(current_user.user_id)
    err = _check_owner(svc, request.dataset_id, owner_id)
    if err:
        return err
    return svc.process_dataset().get_sample(request)


@router.post("/process", response_model=DatasetProcessResponse)
def process_dataset(
    request: DatasetProcessRequest,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    owner_id = int(current_user.user_id)
    err = _check_owner(svc, request.dataset_id, owner_id)
    if err:
        return err
    return svc.process_dataset().process(request)


class ProcessCallbackRequest(BaseModel):
    job_id: str
    dataset_id: int
    status: str = ""
    output_path: Optional[str] = None
    error: Optional[str] = None


def _is_internal_ip(client_ip: str) -> bool:
    """仅接受本地回环或私有网络 IP（容器网络）。"""
    import ipaddress

    if not client_ip:
        return False
    try:
        addr = ipaddress.ip_address(client_ip)
        return addr.is_loopback or addr.is_private
    except ValueError:
        return False


@router.post("/process/callback", response_model=DatasetProcessResponse)
def process_callback(
    request: ProcessCallbackRequest,
    req: Request,
    svc: ServiceFactory = Depends(get_services),
):
    """Celery worker 回调：仅接受本地/容器网络请求。

    支持反向代理：优先使用 X-Forwarded-For 头获取真实客户端 IP。
    """
    forwarded = req.headers.get("X-Forwarded-For", "")
    client_ip = forwarded.split(",")[0].strip() if forwarded else ""
    if not client_ip and req.client:
        client_ip = req.client.host
    if not _is_internal_ip(client_ip):
        return JSONResponse(
            content={"success": False, "error": "Forbidden"},
            status_code=403,
        )
    return svc.process_dataset().check_job(request.job_id, request.dataset_id)


# ══════════════════════════════════════════════════════════
# 下载
# ══════════════════════════════════════════════════════════


@router.post("/download", response_model=DatasetDownloadTokenResponse)
def request_download_token(
    request: DatasetDownloadRequest,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    owner_id = int(current_user.user_id)
    err = _check_owner(svc, request.dataset_id, owner_id)
    if err:
        return err

    info = svc.dataset_import_export().download(request)
    if info.error:
        return JSONResponse(
            content={"success": False, "error": info.error}, status_code=404
        )

    token = svc.jwt().generate_download_token(
        dataset_id=request.dataset_id,
        user_id=owner_id,
    )
    return DatasetDownloadTokenResponse(
        download_token=token,
        filename=info.filename or "",
        file_size=info.file_size or 0,
        format=info.format or "",
        sha256=info.sha256 or "",
    )


@download_router.get("/down_dataset/{token}")
def download_by_token(
    token: str,
    request: Request,
    svc: ServiceFactory = Depends(get_services),
):
    payload = svc.jwt().verify_download_token(token)
    if payload is None:
        return JSONResponse(
            {"success": False, "error": "Invalid or expired download token."},
            status_code=401,
        )

    dataset_id = payload["dataset_id"]
    ds = svc.dataset_repo.find_by_id(dataset_id)
    if ds is None:
        return JSONResponse(
            {"success": False, "error": f"Dataset not found: {dataset_id}"},
            status_code=404,
        )

    file_path = ds.meta.file_path
    if not file_path:
        return JSONResponse(
            {"success": False, "error": "File path not set"}, status_code=404
        )

    from pathlib import Path

    if not Path(file_path).exists():
        return JSONResponse(
            {"success": False, "error": "File not found on disk"}, status_code=404
        )

    return FileResponse(
        path=file_path,
        filename=f"{ds.name}.{ds.meta.format}",
        media_type="application/octet-stream",
    )


# ══════════════════════════════════════════════════════════
# 删除
# ══════════════════════════════════════════════════════════


@datasets_router.delete("", response_model=DatasetRemoveResponse)
def delete_dataset(
    request: DatasetRemoveRequest,
    current_user: TokenPayload = Depends(get_current_user),
    svc: ServiceFactory = Depends(get_services),
):
    owner_id = int(current_user.user_id)
    result = svc.remove_datasets().execute(request, owner_id)
    if not result.deleted:
        return JSONResponse(content=result.model_dump(mode='json'), status_code=404)
    return result


logs_router = APIRouter(prefix="/dataset", tags=["dataset"])


class DatasetLogResponse(BaseModel):
    lines: List[str] = []
    error: Optional[str] = None


@logs_router.get("/logs")
def get_dataset_logs(
    job_id: str = Query(...),
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    """根据 job_id 查询清洗任务的日志文件内容。"""
    import os

    log_repo = svc.dataset_log_repo
    record = log_repo.find_by_job_id(job_id)
    if record is None:
        return DatasetLogResponse(error="日志未找到")

    if not os.path.isfile(record.log_path):
        return DatasetLogResponse(error="日志文件已过期")

    with open(record.log_path, "r", encoding="utf-8") as f:
        lines = [line.rstrip("\n") for line in f.readlines()]
    return DatasetLogResponse(lines=lines)
