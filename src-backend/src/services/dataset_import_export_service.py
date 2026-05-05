"""数据集导入导出服务：分块上传、本地导入、下载。"""

from __future__ import annotations

import hashlib
import logging
import os
import shutil
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

_logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field

from src.core.config import config
from src.core.dataset import Dataset, DatasetMeta
from src.services.interfaces.dataset_repository import DatasetRepository
from src.services.interfaces.file_repository import FileRepository

# ══════════════════════════════════════════════════════════
# 请求 / 响应 — 本地导入 & 下载
# ══════════════════════════════════════════════════════════


class DatasetImportRequest(BaseModel):
    """数据集导入/创建请求。"""

    name: str = Field(..., min_length=1, max_length=100)
    desc: str | None = Field(None, max_length=500)
    tag_ids: list[uuid.UUID] = Field(default_factory=list)
    file_path: str


class DatasetDownloadRequest(BaseModel):
    """数据集导出/下载请求。"""

    dataset_id: uuid.UUID


class DatasetImportExportResponse(BaseModel):
    """数据集导入/导出/下载统一响应。"""

    success: bool = False
    dataset_id: uuid.UUID | None = None
    filename: str | None = None
    file_path: str | None = None
    file_size: int | None = None
    format: str | None = None
    sha256: str | None = None
    error: str | None = None


# ══════════════════════════════════════════════════════════
# 请求 / 响应 — 分块上传
# ══════════════════════════════════════════════════════════


class InitiateUploadRequest(BaseModel):
    filename: str
    file_size: int
    file_hash: str = Field(..., description="客户端 SHA-256")
    chunk_size: int = Field(
        default=5 * 1024 * 1024, ge=1 * 1024 * 1024, le=10 * 1024 * 1024
    )


class InitiateUploadResponse(BaseModel):
    upload_id: str
    chunk_size: int
    total_chunks: int
    uploaded_chunks: list[int] = Field(default_factory=list)
    is_instant_complete: bool = False


class UploadChunkResponse(BaseModel):
    upload_id: str
    chunk_index: int
    received: bool = False
    error: Optional[str] = None


class CompleteUploadRequest(BaseModel):
    upload_id: str
    owner_id: uuid.UUID
    name: str
    desc: str | None = None
    tag_ids: list[uuid.UUID] = Field(default_factory=list)


class CompleteUploadResponse(BaseModel):
    dataset_id: uuid.UUID | None = None
    file_path: str = ""
    success: bool = False
    error: str | None = None


class UploadStatusResponse(BaseModel):
    upload_id: str
    uploaded_chunks: list[int] = []
    total_chunks: int = 0
    is_complete: bool = False


class DatasetDownloadTokenResponse(BaseModel):
    download_token: str
    filename: str
    file_size: int
    format: str
    sha256: str
    error: Optional[str] = None


# ══════════════════════════════════════════════════════════
# 上传会话（内存状态）
# ══════════════════════════════════════════════════════════


class _UploadSession:
    def __init__(self, filename: str, file_size: int, file_hash: str, chunk_size: int):
        self.filename = filename
        self.file_size = file_size
        self.file_hash = file_hash
        self.chunk_size = chunk_size
        self._total_chunks = (file_size + chunk_size - 1) // chunk_size
        self.received_chunks: set[int] = set()
        self.created_at = datetime.now()
        self._finalizing = False

    @property
    def is_complete(self) -> bool:
        return len(self.received_chunks) == self._total_chunks

    @property
    def total_chunks(self) -> int:
        return self._total_chunks


class _UploadState:
    """线程安全的上传会话管理器。"""

    def __init__(self):
        self._sessions: Dict[str, _UploadSession] = {}
        self._lock = threading.Lock()

    def create(
        self, filename: str, file_size: int, file_hash: str, chunk_size: int
    ) -> str:
        upload_id = uuid.uuid4().hex
        with self._lock:
            self._sessions[upload_id] = _UploadSession(
                filename, file_size, file_hash, chunk_size
            )
        return upload_id

    def get(self, upload_id: str) -> Optional[_UploadSession]:
        with self._lock:
            return self._sessions.get(upload_id)

    def mark_received(self, upload_id: str, chunk_index: int) -> bool:
        with self._lock:
            session = self._sessions.get(upload_id)
            if session is None:
                return False
            session.received_chunks.add(chunk_index)
            return True

    def mark_finalizing(self, upload_id: str) -> bool:
        """原子标记会话为处理中，防止并发重复完成。"""
        with self._lock:
            session = self._sessions.get(upload_id)
            if session is None or session._finalizing:
                return False
            session._finalizing = True
            return True

    def remove(self, upload_id: str):
        with self._lock:
            self._sessions.pop(upload_id, None)

    def get_uploaded_chunks(self, upload_id: str) -> list[int]:
        with self._lock:
            session = self._sessions.get(upload_id)
            if session is None:
                return []
            return sorted(session.received_chunks)


# ⚠️ 部署限制：上传会话状态存储在进程内存中。
# 多 worker 部署（uvicorn --workers > 1）时，分块上传请求可能被路由到
# 不同 worker 导致 session 丢失。生产环境请使用单 worker 部署，或迁移至
# Redis 共享存储。
_upload_state = _UploadState()


# ══════════════════════════════════════════════════════════
# 路径工具
# ══════════════════════════════════════════════════════════


def _datasets_dir() -> Path:
    p = Path(config.DATASETS_DIR)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _chunks_dir(upload_id: str) -> Path:
    p = Path(config.DATASETS_DIR) / "chunks" / upload_id
    p.mkdir(parents=True, exist_ok=True)
    return p


# ══════════════════════════════════════════════════════════
# 工具
# ══════════════════════════════════════════════════════════


def _compute_sha256(file_path: str) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(64 * 1024):
            h.update(chunk)
    return h.hexdigest()


def _ensure_indexes(repo) -> None:
    ensure = getattr(repo, "ensure_indexes", None)
    if callable(ensure):
        ensure()


def _drop_indexes(repo) -> None:
    drop = getattr(repo, "drop_indexes", None)
    if callable(drop):
        drop()


def _rollback(repo, dataset_id, final_path, indexes_created) -> None:
    if indexes_created:
        _drop_indexes(repo)
    if final_path is not None:
        final_path.unlink(missing_ok=True)
    if dataset_id is not None:
        repo.remove(dataset_id)


class HashMismatchError(Exception):
    """文件哈希校验失败。"""

    pass


# ══════════════════════════════════════════════════════════
# 服务
# ══════════════════════════════════════════════════════════


class DatasetImportExportService:
    """数据集导入导出统一服务。

    分块上传: initiate → upload_chunk → get_status → complete
    本地导入: import_dataset (本地文件直接入库)
    下载:     download (文件信息 + SHA-256)
    """

    def __init__(
        self,
        dataset_repo: DatasetRepository,
        file_repo: FileRepository,
    ) -> None:
        self._dataset_repo = dataset_repo
        self._file_repo = file_repo

    # ── 分块上传 ──────────────────────────────────────────────

    def initiate(self, request: InitiateUploadRequest) -> InitiateUploadResponse:
        upload_id = _upload_state.create(
            filename=request.filename,
            file_size=request.file_size,
            file_hash=request.file_hash,
            chunk_size=request.chunk_size,
        )
        session = _upload_state.get(upload_id)
        assert session is not None
        _logger.info(
            "Upload initiated: upload_id=%s filename=%s file_size=%d",
            upload_id,
            request.filename,
            request.file_size,
        )
        return InitiateUploadResponse(
            upload_id=upload_id,
            chunk_size=request.chunk_size,
            total_chunks=session.total_chunks,
        )

    def upload_chunk(
        self, upload_id: str, chunk_index: int, data: bytes
    ) -> UploadChunkResponse:
        session = _upload_state.get(upload_id)
        if session is None:
            return UploadChunkResponse(
                upload_id=upload_id,
                chunk_index=chunk_index,
                error="Unknown upload_id",
            )
        chunk_path = _chunks_dir(upload_id) / str(chunk_index)
        chunk_path.write_bytes(data)
        _upload_state.mark_received(upload_id, chunk_index)
        return UploadChunkResponse(
            upload_id=upload_id, chunk_index=chunk_index, received=True
        )

    def get_status(self, upload_id: str) -> dict:
        chunks = _upload_state.get_uploaded_chunks(upload_id)
        session = _upload_state.get(upload_id)
        return {
            "upload_id": upload_id,
            "uploaded_chunks": chunks,
            "total_chunks": session._total_chunks if session else 0,
            "is_complete": session.is_complete if session else False,
        }

    def complete(self, request: CompleteUploadRequest) -> CompleteUploadResponse:
        if not _upload_state.mark_finalizing(request.upload_id):
            return CompleteUploadResponse(
                error=f"Upload already being processed or unknown: {request.upload_id}"
            )
        _logger.info(
            "Upload completing: upload_id=%s owner_id=%d",
            request.upload_id,
            request.owner_id,
        )
        session = _upload_state.get(request.upload_id)
        assert session is not None
        if not session.is_complete:
            return CompleteUploadResponse(
                error=f"Not all chunks received: {len(session.received_chunks)}/{session._total_chunks}"
            )

        chunk_dir = _chunks_dir(request.upload_id)
        dataset_id: Optional[int] = None
        final_path: Optional[Path] = None
        indexes_created = False

        try:
            ext = os.path.splitext(session.filename)[1].lstrip(".").lower()
            if ext not in ("csv", "xlsx", "json"):
                ext = "json"

            meta = DatasetMeta(format=ext, file_path="", file_size=session.file_size)
            now = datetime.now()
            dataset_id = uuid.uuid4()
            entity = Dataset(
                id=dataset_id,
                owner_id=request.owner_id,
                name=request.name,
                desc=request.desc,
                meta=meta,
                status=0,
                tag_ids=request.tag_ids,
                created_at=now,
                updated_at=now,
            )

            self._dataset_repo.create(entity)
            final_path = _datasets_dir() / f"{dataset_id}.{ext}"
            with open(final_path, "wb") as out:
                for i in range(session._total_chunks):
                    cf = chunk_dir / str(i)
                    if cf.exists():
                        out.write(cf.read_bytes())

            actual_hash = _compute_sha256(str(final_path))
            if actual_hash != session.file_hash:
                raise HashMismatchError(
                    f"Hash mismatch: expected {session.file_hash[:16]}..., got {actual_hash[:16]}..."
                )

            entity.meta.file_path = str(final_path.resolve())
            assert dataset_id is not None
            err = self._dataset_repo.update(dataset_id, entity)
            if err is not None:
                raise RuntimeError(f"Failed to update dataset file_path: {err}")

            _ensure_indexes(self._dataset_repo)
            indexes_created = True

            shutil.rmtree(chunk_dir, ignore_errors=True)
            _upload_state.remove(request.upload_id)

            return CompleteUploadResponse(
                dataset_id=dataset_id,
                file_path=str(final_path.resolve()),
                success=True,
            )

        except HashMismatchError as exc:
            _rollback(self._dataset_repo, dataset_id, final_path, indexes_created)
            _logger.exception("Hash mismatch during upload completion")
            return CompleteUploadResponse(error=str(exc))
        except Exception:
            _rollback(self._dataset_repo, dataset_id, final_path, indexes_created)
            _logger.exception("Upload failed for upload_id=%s", request.upload_id)
            return CompleteUploadResponse(error="Upload failed. Please try again.")

    # ── 本地导入 ──────────────────────────────────────────────

    def import_dataset(
        self, request: DatasetImportRequest, owner_id: uuid.UUID
    ) -> DatasetImportExportResponse:
        dataset_id: Optional[int] = None
        indexes_created = False

        try:
            file_path = request.file_path
            file_format = self._file_repo.get_file_ext(file_path).lstrip(".")

            if not self._file_repo.exists(file_path):
                return DatasetImportExportResponse(
                    success=False, error=f"File not found: {file_path}"
                )
            if file_format not in ("csv", "xlsx", "json"):
                return DatasetImportExportResponse(
                    success=False, error=f"Unsupported file type: {file_format}"
                )

            sha256 = _compute_sha256(file_path)
            meta = DatasetMeta(
                format=file_format,
                file_path=file_path,
                file_size=self._file_repo.get_size(file_path),
            )
            now = datetime.now()
            dataset_id = uuid.uuid4()
            entity = Dataset(
                id=dataset_id,
                owner_id=owner_id,
                name=request.name,
                desc=request.desc,
                meta=meta,
                status=0,
                tag_ids=request.tag_ids,
                created_at=now,
                updated_at=now,
            )

            self._dataset_repo.create(entity)
            _ensure_indexes(self._dataset_repo)
            indexes_created = True

            return DatasetImportExportResponse(
                success=True,
                dataset_id=dataset_id,
                filename=f"{request.name}.{file_format}",
                file_path=file_path,
                file_size=meta.file_size,
                format=file_format,
                sha256=sha256,
            )

        except Exception:
            _logger.exception("Import failed for file_path=%s", request.file_path)
            if indexes_created:
                _drop_indexes(self._dataset_repo)
            if dataset_id is not None:
                self._dataset_repo.remove(dataset_id)
            return DatasetImportExportResponse(
                success=False, error="Import failed. Please try again."
            )

    # ── 下载 ──────────────────────────────────────────────────

    def download(self, request: DatasetDownloadRequest) -> DatasetImportExportResponse:
        ds = self._dataset_repo.find_by_id(request.dataset_id)
        if ds is None:
            return DatasetImportExportResponse(
                success=False, error=f"Dataset not found: {request.dataset_id}"
            )

        file_path = ds.meta.file_path
        if not self._file_repo.exists(file_path):
            return DatasetImportExportResponse(
                success=False, error=f"File not found: {file_path}"
            )

        try:
            sha256 = _compute_sha256(file_path)
        except Exception:
            _logger.exception("Hash computation failed for file_path=%s", file_path)
            return DatasetImportExportResponse(
                success=False, error="Failed to compute file hash."
            )

        return DatasetImportExportResponse(
            success=True,
            dataset_id=ds.id,
            filename=f"{ds.name}.{ds.meta.format}",
            file_path=file_path,
            file_size=ds.meta.file_size,
            format=ds.meta.format,
            sha256=sha256,
        )
