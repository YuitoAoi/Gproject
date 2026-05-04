"""ChunkedUploadService 集成测试：分块→续传→校验→组装→秒传"""
import hashlib
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

_PROJECT = Path(__file__).resolve().parent.parent
if str(_PROJECT) not in sys.path:
    sys.path.insert(0, str(_PROJECT))
_SVC = str(_PROJECT / "src" / "services")
if _SVC not in sys.path:
    sys.path.insert(0, _SVC)

from src.core.dataset import Dataset, DatasetMeta
from src.services.dataset_import_export_service import (
    DatasetImportExportService,
    CompleteUploadRequest,
    InitiateUploadRequest,
    _upload_state,
)


@pytest.fixture(autouse=True)
def _clean_upload_state():
    """每个测试前清空上传会话状态。"""
    _upload_state._sessions.clear()
    yield
    _upload_state._sessions.clear()


def _compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class TestChunkedUploadService:

    def test_initiate(self):
        svc = DatasetImportExportService(MagicMock(), MagicMock())
        req = InitiateUploadRequest(
            filename="test.csv", file_size=100, file_hash="abc",
        )
        resp = svc.initiate(req)
        assert resp.upload_id
        assert resp.total_chunks > 0

    def test_upload_chunk(self):
        svc = DatasetImportExportService(MagicMock(), MagicMock())
        req = InitiateUploadRequest(
            filename="test.csv", file_size=10, file_hash="abc",
            chunk_size=10 * 1024 * 1024,
        )
        initiated = svc.initiate(req)
        resp = svc.upload_chunk(initiated.upload_id, 0, b"hello")
        assert resp.received is True

    def test_upload_chunk_unknown_id(self):
        svc = DatasetImportExportService(MagicMock(), MagicMock())
        resp = svc.upload_chunk("bad_id", 0, b"x")
        assert resp.received is False
        assert resp.error is not None

    def test_get_status(self):
        svc = DatasetImportExportService(MagicMock(), MagicMock())
        req = InitiateUploadRequest(
            filename="test.csv", file_size=20, file_hash="abc",
            chunk_size=10 * 1024 * 1024,
        )
        initiated = svc.initiate(req)
        svc.upload_chunk(initiated.upload_id, 0, b"a" * 10)
        status = svc.get_status(initiated.upload_id)
        assert status["upload_id"] == initiated.upload_id
        assert status["total_chunks"] == 1
        assert status["is_complete"] is True

    def test_complete_hash_mismatch(self):
        data = b"hello world"
        mock_ds = MagicMock()
        mock_ds.create.return_value = None
        mock_file = MagicMock()

        svc = DatasetImportExportService(mock_ds, mock_file)
        req = InitiateUploadRequest(
            filename="test.csv", file_size=len(data),
            file_hash=_compute_sha256(b"different data"),
            chunk_size=10 * 1024 * 1024,
        )
        initiated = svc.initiate(req)
        svc.upload_chunk(initiated.upload_id, 0, data)

        complete = CompleteUploadRequest(
            upload_id=initiated.upload_id, owner_id=1, name="test",
        )
        resp = svc.complete(complete)
        assert resp.success is False
        assert "Hash mismatch" in resp.error
