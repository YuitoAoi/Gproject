"""DatasetProcessService 单元测试"""
from unittest.mock import MagicMock, patch

import pytest

from src.core.dataset import DatasetMeta
from src.services.dataset_process_service import (
    DatasetProcessService,
    DatasetProcessRequest,
    SampleRequest,
    DatasetProcessResponse,
)


class TestProcessService:

    @pytest.fixture
    def mock_ds_repo(self):
        repo = MagicMock()
        repo.find.return_value = None
        return repo

    @pytest.fixture
    def mock_file_repo(self):
        fr = MagicMock()
        fr.exists.return_value = True
        fr.get_file_ext.return_value = ".csv"
        fr.get_size.return_value = 100
        return fr

    @pytest.fixture
    def mock_gg(self):
        return MagicMock()

    @pytest.fixture
    def svc(self, mock_ds_repo, mock_file_repo, mock_gg):
        return DatasetProcessService(mock_ds_repo, mock_file_repo, mock_gg)

    # ── get_sample ────────────────────────────────────────

    def test_sample_not_found(self, svc, mock_ds_repo):
        mock_ds_repo.find.return_value = None
        resp = svc.get_sample(SampleRequest(dataset_id=1, limit=10))
        assert resp.error is not None
        assert "not found" in resp.error

    @patch("src.services.dataset_process_service.csv")
    @patch("src.services.dataset_process_service.io")
    def test_sample_csv(self, mock_io, mock_csv, svc, mock_ds_repo, mock_file_repo):
        ds = MagicMock()
        ds.meta = DatasetMeta(format="csv", file_path="/t.csv", file_size=100)
        mock_ds_repo.find.return_value = ds

        mock_csv.reader.return_value = iter([["name", "age"], ["Alice", "30"]])
        mock_file_repo.read.return_value = b"name,age\nAlice,30\n"

        resp = svc.get_sample(SampleRequest(dataset_id=1, limit=10))
        assert resp.columns == ["name", "age"]

    def test_sample_file_not_found(self, svc, mock_ds_repo, mock_file_repo):
        ds = MagicMock()
        ds.meta = DatasetMeta(format="csv", file_path="/missing.csv", file_size=0)
        mock_ds_repo.find.return_value = ds
        mock_file_repo.exists.return_value = False

        resp = svc.get_sample(SampleRequest(dataset_id=1, limit=10))
        assert "not found" in resp.error


    # ── process ───────────────────────────────────────────

    def test_process_not_found(self, svc, mock_ds_repo):
        mock_ds_repo.find.return_value = None
        req = _make_process_req()
        resp = svc.process(req)
        assert resp.status == "failed"
        assert "not found" in resp.error

    def test_process_already_processed(self, svc, mock_ds_repo):
        ds = MagicMock()
        ds.status = 1
        mock_ds_repo.find.return_value = ds
        req = _make_process_req()
        resp = svc.process(req)
        assert resp.status == "failed"
        assert "already processed" in resp.error

    def test_process_success(self, svc, mock_ds_repo, mock_file_repo, mock_gg):
        ds = MagicMock()
        ds.status = 0
        ds.meta = DatasetMeta(format="csv", file_path="/t.csv", file_size=100)
        mock_ds_repo.find.return_value = ds

        mock_resp = MagicMock()
        mock_resp.is_error = False
        mock_resp.json.return_value = {"job_id": "j1", "status": "pending"}
        mock_gg.submit_job.return_value = mock_resp

        resp = svc.process(_make_process_req())
        assert resp.job_id == "j1"
        assert resp.status == "pending"

    def test_process_file_not_found(self, svc, mock_ds_repo, mock_file_repo):
        ds = MagicMock()
        ds.status = 0
        ds.meta = DatasetMeta(format="csv", file_path="/missing.csv", file_size=0)
        mock_ds_repo.find.return_value = ds
        mock_file_repo.exists.return_value = False

        resp = svc.process(_make_process_req())
        assert resp.status == "failed"
        assert "not found" in resp.error

    def test_process_graphgen_error(self, svc, mock_ds_repo, mock_file_repo, mock_gg):
        ds = MagicMock()
        ds.status = 0
        ds.meta = DatasetMeta(format="csv", file_path="/t.csv", file_size=100)
        mock_ds_repo.find.return_value = ds

        mock_resp = MagicMock()
        mock_resp.is_error = True
        mock_resp.json.return_value = {"detail": "API error"}
        mock_resp.text = "error body"
        mock_gg.submit_job.return_value = mock_resp

        resp = svc.process(_make_process_req())
        assert resp.status == "failed"
        assert resp.error != ""

    # ── get_job ───────────────────────────────────────────

    def test_get_job_success(self, svc, mock_gg):
        mock_resp = MagicMock()
        mock_resp.is_error = False
        mock_resp.json.return_value = {
            "job_id": "j1", "status": "running",
            "created_at": "2024-01-01T00:00:00",
            "started_at": None, "finished_at": None,
            "progress": 0.5, "error": None, "output_path": None,
        }
        mock_gg.get_job.return_value = mock_resp

        resp = svc.get_job("j1")
        assert resp.job_id == "j1"
        assert resp.status == "running"
        assert resp.progress == 0.5

    def test_get_job_error(self, svc, mock_gg):
        mock_resp = MagicMock()
        mock_resp.is_error = True
        mock_resp.json.side_effect = ValueError
        mock_resp.status_code = 404
        mock_resp.text = "not found"
        mock_gg.get_job.return_value = mock_resp

        resp = svc.get_job("j1")
        assert resp.status == "failed"

    # ── cancel_job ────────────────────────────────────────

    def test_cancel_job_success(self, svc, mock_gg):
        mock_resp = MagicMock()
        mock_resp.is_error = False
        mock_resp.json.return_value = {"job_id": "j1", "status": "cancelled"}
        mock_gg.cancel_job.return_value = mock_resp

        resp = svc.cancel_job("j1")
        assert resp.status == "cancelled"

    def test_cancel_job_error(self, svc, mock_gg):
        mock_resp = MagicMock()
        mock_resp.is_error = True
        mock_resp.json.side_effect = ValueError
        mock_resp.status_code = 404
        mock_resp.text = "not found"
        mock_gg.cancel_job.return_value = mock_resp

        resp = svc.cancel_job("j1")
        assert resp.status == "failed"


def _make_process_req():
    return DatasetProcessRequest(
        dataset_id=1, api_key="k", synthesizer_url="u",
        synthesizer_model="m", mode="atomic", data_format="Alpaca",
    )
