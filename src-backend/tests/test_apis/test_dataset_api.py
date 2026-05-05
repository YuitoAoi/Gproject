"""Dataset API 端点集成测试"""
import sys
import uuid
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

_PROJECT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT) not in sys.path:
    sys.path.insert(0, str(_PROJECT))

_UID = uuid.UUID("00000000-0000-0000-0000-000000000001")
_UID_S = str(_UID)
_DID = uuid.UUID("00000000-0000-0000-0000-0000000000a1")
_DID_S = str(_DID)
_NF = uuid.UUID("00000000-0000-0000-0000-000000000999")
_NF_S = str(_NF)


def _make_token_payload(user_id=_UID_S):
    from src.services.jwt_service import TokenPayload
    return TokenPayload(user_id=user_id, email="admin@test.com", exp=9999999999)


def _build_test_app():
    app = FastAPI()

    from src.app.v1.dataset import router as ds_router, datasets_router, download_router
    app.include_router(ds_router)
    app.include_router(datasets_router)
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

    # ═══ GET /datasets ═══════════════════════════════════════

    def test_list_empty(self, client):
        tc, mock_svc = client
        from src.services.dataset_get_service import GetDatasetsResponse
        mock_svc.get_datasets.return_value.get_all.return_value = \
            GetDatasetsResponse(items=[], total=0)
        resp = tc.get("/datasets", **_auth())
        assert resp.status_code == 200
        assert resp.json()["items"] == []

    def test_list_with_data(self, client):
        tc, mock_svc = client
        from src.services.dataset_get_service import GetDatasetsResponse
        now = datetime.now()
        ds = {
            "id": _DID_S, "name": "test", "desc": None,
            "format": "json", "file_size": 1024,
            "status": 0, "tag_ids": [], "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        mock_svc.get_datasets.return_value.get_all.return_value = \
            GetDatasetsResponse(items=[ds], total=1)
        resp = tc.get("/datasets", **_auth())
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    # ═══ POST /dataset/get ══════════════════════════════════

    def test_get_by_id_found(self, client):
        tc, mock_svc = client
        from src.services.dataset_get_service import GetDatasetResponse
        now = datetime.now()
        ds = {
            "id": _DID_S, "name": "test", "desc": None,
            "format": "json", "file_size": 1024,
            "status": 0, "tag_ids": [], "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        mock_svc.get_datasets.return_value.get_by_id.return_value = \
            GetDatasetResponse(dataset=ds)
        resp = tc.post("/dataset/get", json={"dataset_id": _DID_S}, **_auth())
        assert resp.status_code == 200
        assert resp.json()["dataset"]["name"] == "test"

    def test_get_by_id_not_found(self, client):
        tc, mock_svc = client
        from src.services.dataset_get_service import GetDatasetResponse
        mock_svc.get_datasets.return_value.get_by_id.return_value = \
            GetDatasetResponse(error="Dataset not found: 999")
        resp = tc.post("/dataset/get", json={"dataset_id": _NF_S}, **_auth())
        assert resp.status_code == 404

    # ═══ POST /dataset/upload/initiate ══════════════════════

    def test_upload_initiate(self, client):
        tc, mock_svc = client
        from src.services.dataset_import_export_service import InitiateUploadResponse
        mock_svc.chunked_upload.return_value.initiate.return_value = \
            InitiateUploadResponse(upload_id="abc123", chunk_size=5242880, total_chunks=3)
        resp = tc.post("/dataset/upload/initiate", json={
            "filename": "test.json", "file_size": 15000000, "file_hash": "sha256hex",
        }, **_auth())
        assert resp.status_code == 200
        assert resp.json()["upload_id"] == "abc123"

    # ═══ POST /dataset/sample ═══════════════════════════════

    def test_get_sample(self, client):
        tc, mock_svc = client
        from src.services.dataset_process_service import SampleResponse
        mock_svc.dataset_repo.find_by_id.return_value = MagicMock(owner_id=_UID)
        mock_svc.process_dataset.return_value.get_sample.return_value = \
            SampleResponse(columns=["Q", "A"], rows=[{"Q": "x", "A": "y"}], total_rows=100)
        resp = tc.post("/dataset/sample", json={"dataset_id": _DID_S, "limit": 50}, **_auth())
        assert resp.status_code == 200
        assert resp.json()["columns"] == ["Q", "A"]

    # ═══ POST /dataset/process ═════════════════════════════

    def test_process_clean(self, client):
        tc, mock_svc = client
        from src.services.dataset_process_service import DatasetProcessResponse
        mock_svc.dataset_repo.find_by_id.return_value = MagicMock(owner_id=_UID)
        mock_svc.process_dataset.return_value.process.return_value = \
            DatasetProcessResponse(job_id="task-123", status="pending")
        resp = tc.post("/dataset/process", json={
            "dataset_id": _DID_S,
            "api_key": "sk-xxx",
            "synthesizer_url": "https://api.example.com/v1",
            "synthesizer_model": "Qwen/Qwen2.5-7B-Instruct",
            "mode": "atomic",
            "data_format": "Alpaca",
        }, **_auth())
        assert resp.status_code == 200
        assert resp.json()["job_id"] == "task-123"

    def test_process_missing_body(self, client):
        tc, _ = client
        resp = tc.post("/dataset/process", json={}, **_auth())
        assert resp.status_code == 422

    # ═══ POST /dataset/download ════════════════════════════

    def test_request_download_token(self, client):
        tc, mock_svc = client
        from src.services.dataset_import_export_service import DatasetImportExportResponse
        mock_svc.dataset_repo.find_by_id.return_value = MagicMock(owner_id=_UID)
        mock_svc.dataset_import_export.return_value.download.return_value = \
            DatasetImportExportResponse(
                success=True, dataset_id=_DID, filename="test.json",
                file_size=1024, format="json", sha256="abc",
            )
        mock_svc.jwt.return_value.generate_download_token.return_value = "token-xyz"
        resp = tc.post("/dataset/download", json={"dataset_id": _DID_S}, **_auth())
        assert resp.status_code == 200
        assert resp.json()["filename"] == "test.json"

    # ═══ Auth ═══════════════════════════════════════════════

    def test_no_auth_header(self, client):
        tc, _ = client
        assert tc.get("/datasets").status_code == 401

    def test_invalid_token_format(self, client):
        tc, _ = client
        resp = tc.get("/datasets", headers={"Authorization": "Basic abc"})
        assert resp.status_code == 401

    # ═══ DELETE /datasets ═══════════════════════════════════

    def test_delete_success(self, client):
        tc, mock_svc = client
        from src.services.dataset_remove_service import DatasetRemoveResponse
        mock_svc.remove_datasets.return_value.execute.return_value = \
            DatasetRemoveResponse(success=True, deleted=[_DID])
        resp = tc.request("DELETE", "/datasets", json={"dataset_ids": [_DID_S]}, **_auth())
        assert resp.status_code == 200
        assert resp.json()["deleted"] == [_DID_S]

    def test_delete_not_found(self, client):
        tc, mock_svc = client
        from src.services.dataset_remove_service import DatasetRemoveResponse
        mock_svc.remove_datasets.return_value.execute.return_value = \
            DatasetRemoveResponse(success=False, errors=[f"Dataset not found: {_NF}"])
        resp = tc.request("DELETE", "/datasets", json={"dataset_ids": [_NF_S]}, **_auth())
        assert resp.status_code == 404

    # ═══ GET /down_dataset/{token} ═════════════════════════

    def test_download_by_token_invalid(self, client):
        tc, mock_svc = client
        mock_svc.jwt.return_value.verify_download_token.return_value = None
        resp = tc.get("/down_dataset/expired-token")
        assert resp.status_code == 401
