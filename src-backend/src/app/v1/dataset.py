from fastapi import APIRouter, Depends, Request, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse

from src.app.dependencies import get_current_user, get_services
from src.services import (
    GetDatasetResponse,
    GetDatasetsResponse,
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
)
from src.services.jwt_service import TokenPayload

router = APIRouter(prefix="/dataset", tags=["dataset"])
datasets_router = APIRouter(prefix="/datasets", tags=["dataset"])
download_router = APIRouter(tags=["download"])


def _check_owner(svc: ServiceFactory, dataset_id: int, owner_id: int) -> str | None:
    ds = svc.dataset_repo.find(dataset_id)
    if ds is None:
        return f"Dataset not found: {dataset_id}"
    if ds.owner_id != owner_id:
        return f"Dataset does not belong to this user: {dataset_id}"
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


@router.post("/get", response_model=GetDatasetResponse)
def get_dataset(
    request: DatasetDownloadRequest,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    owner_id = int(current_user.user_id)
    return svc.get_datasets().get_by_id(request.dataset_id, owner_id)


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
        return JSONResponse(content=result.model_dump(), status_code=400)
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
    return svc.chunked_upload().upload_chunk(upload_id, chunk_index, data)


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
        return JSONResponse(content=result.model_dump(), status_code=400)
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
        return JSONResponse(content=result.model_dump(), status_code=400)
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
        return SampleResponse(error=err)
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
        return DatasetProcessResponse(job_id="", status="failed", error=err)
    return svc.process_dataset().process(request)


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
        return DatasetDownloadTokenResponse(download_token="", filename="", file_size=0, format="", sha256="", error=err)

    info = svc.dataset_import_export().download(request)
    if info.error:
        return JSONResponse(content={"error": info.error}, status_code=404)

    token = svc.jwt()._generate_download_token(
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
        return JSONResponse({"error": "Invalid or expired download token."}, status_code=401)

    dataset_id = payload["dataset_id"]
    ds = svc.dataset_repo.find(dataset_id)
    if ds is None:
        return JSONResponse({"error": f"Dataset not found: {dataset_id}"}, status_code=404)

    file_path = ds.meta.file_path
    if not file_path:
        return JSONResponse({"error": "File path not set"}, status_code=404)

    from pathlib import Path
    if not Path(file_path).exists():
        return JSONResponse({"error": "File not found on disk"}, status_code=404)

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
    return svc.remove_datasets().execute(request, owner_id)
