from fastapi import APIRouter, Depends, Request, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse

from src.app.dependencies import get_current_user, get_services
from src.services import (
    GetDatasetResponse,
    GetDatasetsResponse,
    ServiceFactory,
)
from src.services.chunked_upload_service import (
    ChunkedUploadService,
    CompleteUploadRequest,
    CompleteUploadResponse,
    InitiateUploadRequest,
    InitiateUploadResponse,
    UploadChunkResponse,
)
from src.services.dataset_process_service import (
    ProcessRequest,
    ProcessResponse,
    SampleRequest,
    SampleResponse,
)
from src.services.jwt_service import TokenPayload

router = APIRouter(prefix="/dataset", tags=["dataset"])
download_router = APIRouter(tags=["download"])


@router.get("/", response_model=GetDatasetsResponse)
def list_datasets(
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    owner_id = int(current_user.user_id)
    return svc.get_datasets().get_all(owner_id=owner_id)


@router.get("/{dataset_id}", response_model=GetDatasetResponse)
def get_dataset(
    dataset_id: int,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    owner_id = int(current_user.user_id)
    return svc.get_datasets().get_by_id(dataset_id, owner_id)


# ══════════════════════════════════════════════════════════
# 分块上传
# ══════════════════════════════════════════════════════════

@router.post("/upload/initiate", response_model=InitiateUploadResponse)
def initiate_upload(
    request: InitiateUploadRequest,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    """初始化上传，返回 upload_id。"""
    return svc.chunked_upload().initiate(request)


@router.post("/upload/chunk", response_model=UploadChunkResponse)
def upload_chunk(
    upload_id: str = Form(...),
    chunk_index: int = Form(...),
    file: UploadFile = File(...),
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    """上传单个分片 (multipart/form-data)。"""
    data = file.file.read()
    return svc.chunked_upload().upload_chunk(upload_id, chunk_index, data)


@router.get("/upload/{upload_id}/status")
def upload_status(
    upload_id: str,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    """查询上传进度（断点续传）。"""
    return svc.chunked_upload().get_status(upload_id)


@router.post("/upload/complete", response_model=CompleteUploadResponse)
def complete_upload(
    request: CompleteUploadRequest,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    """合并分块 → 校验哈希 → 创建 Dataset 记录。"""
    request.owner_id = int(current_user.user_id)
    return svc.chunked_upload().complete(request)


# ══════════════════════════════════════════════════════════
# 样本 / 处理
# ══════════════════════════════════════════════════════════

@router.get("/{dataset_id}/sample", response_model=SampleResponse)
def get_dataset_sample(
    dataset_id: int,
    limit: int = 100,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    """获取数据集前 N 条样本及表头。"""
    return svc.process_dataset().get_sample(dataset_id, SampleRequest(limit=limit))


@router.post("/{dataset_id}/process", response_model=ProcessResponse)
def process_dataset(
    dataset_id: int,
    request: ProcessRequest,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    """提交数据清洗/格式转换任务。"""
    return svc.process_dataset().process(dataset_id, request)


# ══════════════════════════════════════════════════════════
# 下载
# ══════════════════════════════════════════════════════════

@router.post("/{dataset_id}/download")
def request_download_token(
    dataset_id: int,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    """生成下载令牌。"""
    info = svc.process_dataset().download(dataset_id)
    if info.error:
        return {"error": info.error}

    token = svc.jwt()._generate_download_token(
        dataset_id=dataset_id,
        user_id=int(current_user.user_id),
    )
    return {
        "download_token": token,
        "filename": info.filename,
        "file_size": info.file_size,
        "format": info.format,
    }


@download_router.get("/down_dataset/{token}")
def download_by_token(token: str, request: Request):
    """凭下载令牌获取文件流。"""
    svc: ServiceFactory = request.app.state.services

    payload = svc.jwt().verify_download_token(token)
    if payload is None:
        return JSONResponse(
            {"error": "Invalid or expired download token."}, status_code=401
        )

    dataset_id = payload["dataset_id"]
    ds = svc.dataset_repo.find(dataset_id)
    if ds is None:
        return JSONResponse(
            {"error": f"Dataset not found: {dataset_id}"}, status_code=404
        )

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

@router.delete("/{dataset_id}")
def delete_dataset(
    dataset_id: int,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    """删除数据集（含文件）。"""
    err = svc.dataset_repo.remove(dataset_id)
    if err is not None:
        return {"error": str(err)}
    return {"deleted": str(dataset_id)}
