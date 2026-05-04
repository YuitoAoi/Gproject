"""Dataset API 端点集成测试"""
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

_PROJECT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT) not in sys.path:
    sys.path.insert(0, str(_PROJECT))
_SVC = str(_PROJECT / "src" / "services")
if _SVC not in sys.path:
    sys.path.insert(0, _SVC)

from src.core.dataset import Dataset, DatasetMeta
from src.services.jwt_service import TokenPayload


def _make_meta(format="json", file_path="/data/test.json", file_size=1024):
    return DatasetMeta(format=format, file_path=file_path, file_size=file_size)


def _make_dataset(owner_id=1, name="test", id=1):
    now = datetime.now()
    return Dataset(
        id=id, owner_id=owner_id, name=name, desc="test dataset",
        meta=_make_meta(), status=0, tag_ids=[], created_at=now, updated_at=now,
    )


def _make_token_payload(user_id="1"):
    return TokenPayload(user_id=user_id, email="admin@test.com", exp=9999999999)


def _build_test_app():
    app = FastAPI()

    from src.app.v1.dataset import router as ds_router, download_router
    app.include_router(ds_router)
    app.include_router(download_router)

    mock_jwt = MagicMock()
    mock_jwt.verify_access_token.return_value = _make_token_payload()

    mock_svc = MagicMock()
    mock_svc.jwt.return_value = mock_jwt
    mock_svc.dataset_repo = MagicMock()

    app.state.services = mock_svc

    from src.app.dependencies import get_services
    app.dependency_overrides[get_services] = lambda: mock_svc

    return app, mock_svc


@pytest.fixture
def client():
    app, mock_svc = _build_test_app()
    with TestClient(app) as tc:
        yield tc, mock_svc


def _auth(kwargs=None):
    if kwargs is None:
        kwargs = {}
    kwargs.setdefault("headers", {})["Authorization"] = "Bearer valid-token"
    return kwargs


class TestDatasetAPI:
    """测试 /dataset/* 端点"""

    # ═══ GET / (列表) ═══════════════════════════════════════

    def test_list_empty(self, client):
        tc, mock_svc = client
        from src.services.datasets_get_service import GetDatasetsResponse

        mock_svc.get_datasets.return_value.get_all.return_value = \
            GetDatasetsResponse(items=[], total=0)

        resp = tc.get("/dataset/", **_auth())
        assert resp.status_code == 200
        assert resp.json()["items"] == []

    def test_list_with_data(self, client):
        tc, mock_svc = client
        from src.services.datasets_get_service import GetDatasetsResponse
        ds = _make_dataset()

        mock_svc.get_datasets.return_value.get_all.return_value = \
            GetDatasetsResponse(items=[ds], total=1)

        resp = tc.get("/dataset/", **_auth())
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    # ═══ GET /{id} (详情) ══════════════════════════════════

    def test_get_by_id_found(self, client):
        tc, mock_svc = client
        from src.services.datasets_get_service import GetDatasetResponse
        ds = _make_dataset()

        mock_svc.get_datasets.return_value.get_by_id.return_value = \
            GetDatasetResponse(dataset=ds)

        resp = tc.get("/dataset/1", **_auth())
        assert resp.status_code == 200
        assert resp.json()["dataset"]["name"] == "test"
        # 验证路由传入了 owner_id
        mock_svc.get_datasets.return_value.get_by_id.assert_called_with(1, 1)

    def test_get_by_id_not_found(self, client):
        tc, mock_svc = client
        from src.services.datasets_get_service import GetDatasetResponse

        mock_svc.get_datasets.return_value.get_by_id.return_value = \
            GetDatasetResponse(error="Dataset not found: 999")

        resp = tc.get("/dataset/999", **_auth())
        assert resp.status_code == 200
        assert "error" in resp.json()

    # ═══ POST /upload ══════════════════════════════════════

    def test_upload_initiate(self, client):
        tc, mock_svc = client
        from src.services.chunked_upload_service import InitiateUploadResponse

        mock_svc.chunked_upload.return_value.initiate.return_value = \
            InitiateUploadResponse(upload_id="abc123", chunk_size=5242880, total_chunks=3)

        resp = tc.post("/dataset/upload/initiate", json={
            "filename": "test.json",
            "file_size": 15000000,
            "file_hash": "sha256hex",
        }, **_auth())
        assert resp.status_code == 200
        assert resp.json()["upload_id"] == "abc123"

    # ═══ GET /{id}/sample ═════════════════════════════════

    def test_get_sample(self, client):
        tc, mock_svc = client
        from src.services.dataset_process_service import SampleResponse

        mock_svc.process_dataset.return_value.get_sample.return_value = \
            SampleResponse(columns=["Q", "A"], rows=[{"Q": "x", "A": "y"}], total_rows=100)

        resp = tc.get("/dataset/1/sample?limit=50", **_auth())
        assert resp.status_code == 200
        assert resp.json()["columns"] == ["Q", "A"]

    # ═══ POST /{id}/process ════════════════════════════════

    def test_process_clean(self, client):
        tc, mock_svc = client
        from src.services.dataset_process_service import DatasetProcessResponse

        mock_svc.process_dataset.return_value.process.return_value = \
            DatasetProcessResponse(task_id="task-123", status="pending")

        resp = tc.post("/dataset/1/process", json={
            "process_type": "clean",
            "clean_config": {
                "field_mapping": [
                    {"source_column": "Q", "target_field": "instruction"},
                ],
                "basic_filtering": {"enabled": True},
            },
        }, **_auth())
        assert resp.status_code == 200
        assert resp.json()["task_id"] == "task-123"

    def test_process_missing_body(self, client):
        """缺少必填字段 → 422"""
        tc, _ = client
        resp = tc.post("/dataset/1/process", json={}, **_auth())
        assert resp.status_code == 422

    # ═══ POST /{id}/download (获取令牌) ═══════════════════

    def test_request_download_token(self, client):
        tc, mock_svc = client
        from src.services.dataset_process_service import DownloadResponse

        mock_svc.process_dataset.return_value.download.return_value = \
            DownloadResponse(filename="test.json", file_size=1024, format="json")

        resp = tc.post("/dataset/1/download", **_auth())
        assert resp.status_code == 200
        data = resp.json()
        assert "download_token" in data
        assert data["filename"] == "test.json"

    # ═══ GET /down_dataset/{token} (公开下载) ══════════════

    def test_download_by_token(self, client, tmp_path):
        tc, mock_svc = client
        from src.core.dataset import DatasetMeta

        # 创建临时文件
        test_file = tmp_path / "test.json"
        test_file.write_text('{"a":1}')

        mock_svc.jwt.return_value.verify_download_token.return_value = {
            "user_id": 1, "dataset_id": 1
        }

        ds_meta = DatasetMeta(format="json", file_path=str(test_file), file_size=test_file.stat().st_size)
        from src.core.dataset import Dataset
        from datetime import datetime
        mock_svc.dataset_repo.find.return_value = Dataset(
            id=1, owner_id=1, name="test", meta=ds_meta, status=0,
            created_at=datetime.now(), updated_at=datetime.now(),
        )

        resp = tc.get("/down_dataset/valid-token-123")
        assert resp.status_code == 200

    def test_download_by_token_invalid(self, client):
        tc, mock_svc = client
        mock_svc.jwt.return_value.verify_download_token.return_value = None

        resp = tc.get("/down_dataset/expired-token")
        assert resp.status_code == 401

    # ═══ 401 ════════════════════════════════════════════════

    def test_no_auth_header(self, client):
        tc, _ = client
        assert tc.get("/dataset/").status_code == 401

    def test_invalid_token_format(self, client):
        tc, _ = client
        resp = tc.get("/dataset/", headers={"Authorization": "Basic abc"})
        assert resp.status_code == 401

    # ═══ DELETE /{id} ═══════════════════════════════════════

    def test_delete_success(self, client):
        tc, mock_svc = client
        mock_svc.dataset_repo.remove.return_value = None
        resp = tc.delete("/dataset/1", **_auth())
        assert resp.status_code == 200

    def test_delete_not_found(self, client):
        tc, mock_svc = client
        mock_svc.dataset_repo.remove.return_value = ValueError("Dataset not found")
        resp = tc.delete("/dataset/999", **_auth())
        assert resp.status_code == 200
        assert "error" in resp.json()
