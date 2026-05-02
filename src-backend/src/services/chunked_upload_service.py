"""分块上传服务：initiate → upload_chunk → complete → 创建 Dataset。"""
from __future__ import annotations

import hashlib
import os
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from pydantic import BaseModel, Field

from src.core.config import config
from src.core.dataset import Dataset, DatasetMeta
from src.services.interfaces.dataset_repository import DatasetRepository
from src.services.interfaces.file_repository import FileRepository


# ══════════════════════════════════════════════════════════
# 请求 / 响应模型
# ══════════════════════════════════════════════════════════

class InitiateUploadRequest(BaseModel):
    filename: str
    file_size: int
    file_hash: str = Field(..., description="客户端 SHA-256")
    chunk_size: int = Field(default=5 * 1024 * 1024, ge=1 * 1024 * 1024, le=10 * 1024 * 1024)


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
    owner_id: int
    name: str
    desc: Optional[str] = None
    tag_ids: list[int] = Field(default_factory=list)


class CompleteUploadResponse(BaseModel):
    dataset_id: Optional[int] = None
    file_path: str = ""
    success: bool = False
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
        self.total_chunks = (file_size + chunk_size - 1) // chunk_size
        self.received_chunks: set[int] = set()
        self.created_at = datetime.now()

    @property
    def is_complete(self) -> bool:
        return len(self.received_chunks) == self.total_chunks


class _UploadState:
    """线程安全的上传会话管理器。"""

    def __init__(self):
        self._sessions: Dict[str, _UploadSession] = {}
        self._lock = threading.Lock()

    def create(self, filename: str, file_size: int, file_hash: str,
               chunk_size: int) -> str:
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

    def remove(self, upload_id: str):
        with self._lock:
            self._sessions.pop(upload_id, None)

    def get_uploaded_chunks(self, upload_id: str) -> list[int]:
        with self._lock:
            session = self._sessions.get(upload_id)
            if session is None:
                return []
            return sorted(session.received_chunks)


# 全局上传状态
_upload_state = _UploadState()


# ══════════════════════════════════════════════════════════
# 路径工具
# ══════════════════════════════════════════════════════════

def _datasets_dir() -> Path:
    p = Path(config.DATA_DIR) / "datasets"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _chunks_dir(upload_id: str) -> Path:
    p = Path(config.DATA_DIR) / "chunks" / upload_id
    p.mkdir(parents=True, exist_ok=True)
    return p


def _compute_sha256(file_path: str) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(64 * 1024):
            h.update(chunk)
    return h.hexdigest()


# ══════════════════════════════════════════════════════════
# 服务
# ══════════════════════════════════════════════════════════

class ChunkedUploadService:
    """分块上传用例。

    依赖通过构造函数注入。
    """

    def __init__(
        self,
        dataset_repo: DatasetRepository,
        file_repo: FileRepository,
    ) -> None:
        self._dataset_repo = dataset_repo
        self._file_repo = file_repo

    def initiate(self, request: InitiateUploadRequest) -> InitiateUploadResponse:
        upload_id = _upload_state.create(
            filename=request.filename,
            file_size=request.file_size,
            file_hash=request.file_hash,
            chunk_size=request.chunk_size,
        )
        session = _upload_state.get(upload_id)
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
                upload_id=upload_id, chunk_index=chunk_index,
                error="Unknown upload_id"
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
            "total_chunks": session.total_chunks if session else 0,
            "is_complete": session.is_complete if session else False,
        }

    def complete(
        self, request: CompleteUploadRequest
    ) -> CompleteUploadResponse:
        session = _upload_state.get(request.upload_id)
        if session is None:
            return CompleteUploadResponse(
                error=f"Unknown upload_id: {request.upload_id}"
            )

        if not session.is_complete:
            return CompleteUploadResponse(
                error=f"Not all chunks received: "
                      f"{len(session.received_chunks)}/{session.total_chunks}"
            )

        chunk_dir = _chunks_dir(request.upload_id)

        try:
            # 创建 Dataset 记录（先占位，获取 ID）
            ext = os.path.splitext(session.filename)[1].lstrip(".").lower()
            if ext not in ("csv", "xlsx", "json"):
                ext = "json"

            meta = DatasetMeta(format=ext, file_path="", file_size=session.file_size)
            entity = Dataset.new(
                owner_id=request.owner_id,
                name=request.name,
                desc=request.desc,
                meta=meta,
                tag_ids=request.tag_ids,
            )

            err = self._dataset_repo.create(entity)
            if err is not None:
                return CompleteUploadResponse(error=f"Failed to create dataset: {err}")

            dataset_id = entity.id

            # 合并分块到最终文件: datasets/{id}.{ext}
            final_path = _datasets_dir() / f"{dataset_id}.{ext}"

            with open(final_path, "wb") as out:
                for i in range(session.total_chunks):
                    chunk_file = chunk_dir / str(i)
                    if chunk_file.exists():
                        out.write(chunk_file.read_bytes())

            # 校验文件哈希
            actual_hash = _compute_sha256(str(final_path))
            if actual_hash != session.file_hash:
                # 哈希不匹配，删除文件和不完整记录
                final_path.unlink(missing_ok=True)
                self._dataset_repo.remove(dataset_id)
                return CompleteUploadResponse(
                    error=f"Hash mismatch: expected {session.file_hash[:16]}..., "
                          f"got {actual_hash[:16]}..."
                )

            # 更新 file_path
            entity.meta.file_path = str(final_path.resolve())
            self._dataset_repo.update(dataset_id, entity)

            # 清理分片
            import shutil
            shutil.rmtree(chunk_dir, ignore_errors=True)
            _upload_state.remove(request.upload_id)

            return CompleteUploadResponse(
                dataset_id=dataset_id,
                file_path=str(final_path.resolve()),
                success=True,
            )
        except Exception as exc:
            return CompleteUploadResponse(error=str(exc))
