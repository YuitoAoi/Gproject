"""Dataset 用例层单元测试（mock 仓储）"""
import sys
import uuid
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

_PROJECT = Path(__file__).resolve().parent.parent
if str(_PROJECT) not in sys.path:
    sys.path.insert(0, str(_PROJECT))

from src.core.dataset import Dataset, DatasetMeta
from src.services.dataset_import_export_service import (
    DatasetImportExportService,
    DatasetImportRequest,
    DatasetImportExportResponse,
)
from src.services.dataset_get_service import GetDatasetsService

_DID1 = uuid.uuid4()
_DID2 = uuid.uuid4()
_OID1 = uuid.uuid4()
_OID2 = uuid.uuid4()


def _make_meta(format="json", file_path="/data/test.json", file_size=1024):
    return DatasetMeta(format=format, file_path=file_path, file_size=file_size)


def _make_dataset(owner_id=_OID1, name="test", id=_DID1):
    now = datetime.now()
    return Dataset(
        id=id,
        owner_id=owner_id,
        name=name,
        desc="test dataset",
        meta=_make_meta(),
        created_at=now,
        updated_at=now,
    )


class TestDatasetImportExportService:
    """DatasetImportExportService 单元测试"""

    def test_import_success(self, monkeypatch):
        monkeypatch.setattr(
            "src.services.dataset_import_export_service._compute_sha256",
            lambda path: "abc123",
        )
        mock_file = MagicMock()
        mock_file.get_file_ext.return_value = ".json"
        mock_file.exists.return_value = True
        mock_file.get_size.return_value = 2048

        mock_ds = MagicMock()
        mock_ds.create.return_value = None

        svc = DatasetImportExportService(dataset_repo=mock_ds, file_repo=mock_file)
        req = DatasetImportRequest(name="mydata", desc="test", file_path="/data/test.json")
        resp = svc.import_dataset(req, owner_id=_OID1)

        assert resp.success is True
        mock_ds.create.assert_called_once()

    def test_file_not_found(self):
        mock_file = MagicMock()
        mock_file.exists.return_value = False

        svc = DatasetImportExportService(dataset_repo=MagicMock(), file_repo=mock_file)
        req = DatasetImportRequest(name="x", file_path="/missing.csv")
        resp = svc.import_dataset(req, owner_id=_OID1)

        assert resp.success is False
        assert "not found" in resp.error

    def test_unsupported_format(self):
        mock_file = MagicMock()
        mock_file.get_file_ext.return_value = ".txt"
        mock_file.exists.return_value = True

        svc = DatasetImportExportService(dataset_repo=MagicMock(), file_repo=mock_file)
        req = DatasetImportRequest(name="x", file_path="/bad.txt")
        resp = svc.import_dataset(req, owner_id=_OID1)

        assert resp.success is False
        assert "Unsupported" in resp.error


class TestGetDatasetsService:
    """GetDatasetsService 单元测试"""

    def test_get_all_empty(self):
        mock_repo = MagicMock()
        mock_repo.find_by_owner.return_value = []

        svc = GetDatasetsService(dataset_repo=mock_repo)
        resp = svc.get_all(owner_id=_OID1)

        assert resp.items == []
        assert resp.total == 0
        assert resp.error is None

    def test_get_all_with_data(self):
        ds1 = _make_dataset(owner_id=_OID1, name="my_ds", id=_DID1)
        ds2 = _make_dataset(owner_id=_OID2, name="other_ds", id=_DID2)
        mock_repo = MagicMock()
        mock_repo.find_by_owner.return_value = [ds1]

        svc = GetDatasetsService(dataset_repo=mock_repo)
        resp = svc.get_all(owner_id=_OID1)

        assert resp.total == 1
        assert resp.items[0].name == "my_ds"

    def test_get_by_id_found(self):
        ds = _make_dataset(owner_id=_OID1, id=_DID1, name="myds")
        mock_repo = MagicMock()
        mock_repo.find_by_id.return_value = ds

        svc = GetDatasetsService(dataset_repo=mock_repo)
        resp = svc.get_by_id(_DID1, owner_id=_OID1)

        assert resp.dataset is not None
        assert resp.dataset.name == "myds"
        assert resp.error is None

    def test_get_by_id_not_found(self):
        mock_repo = MagicMock()
        mock_repo.find_by_id.return_value = None

        svc = GetDatasetsService(dataset_repo=mock_repo)
        resp = svc.get_by_id(uuid.uuid4(), owner_id=_OID1)

        assert resp.dataset is None
        assert "not found" in resp.error

    def test_get_by_id_wrong_owner(self):
        ds = _make_dataset(owner_id=_OID2, id=_DID1, name="other")
        mock_repo = MagicMock()
        mock_repo.find_by_id.return_value = ds

        svc = GetDatasetsService(dataset_repo=mock_repo)
        resp = svc.get_by_id(_DID1, owner_id=_OID1)

        assert resp.dataset is None
        assert "Access denied" in resp.error
