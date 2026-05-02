"""Dataset 用例层单元测试（mock 仓储）"""
import sys
from datetime import datetime
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
from src.services.dataset_create_service import (
    CreateDatasetRequest,
    CreateDatasetResponse,
    CreateDatasetService,
)
from src.services.datasets_get_service import GetDatasetsService


def _make_meta(format="json", file_path="/data/test.json", file_size=1024):
    return DatasetMeta(format=format, file_path=file_path, file_size=file_size)


def _make_dataset(owner_id=1, name="test", id=1):
    now = datetime.now()
    return Dataset(
        id=id,
        owner_id=owner_id,
        name=name,
        desc="test dataset",
        meta=_make_meta(),
        status=0,
        tag_ids=[],
        created_at=now,
        updated_at=now,
    )


class TestCreateDatasetService:
    """CreateDatasetService 单元测试"""

    def test_create_success(self):
        """正常文件路径 + 格式校验通过 → success=True"""
        mock_file = MagicMock()
        mock_file.get_file_ext.return_value = ".json"
        mock_file.exists.return_value = True
        mock_file.get_size.return_value = 2048

        mock_ds = MagicMock()
        mock_ds.create.return_value = 1

        svc = CreateDatasetService(dataset_repo=mock_ds, file_repo=mock_file)
        req = CreateDatasetRequest(
            owner_id=1,
            name="mydata",
            desc="test",
            file_path="/data/test.json",
            tag_ids=[],
        )
        resp = svc.execute(req)

        assert resp.success is True
        assert resp.error is None
        mock_ds.create.assert_called_once()

    def test_file_not_found(self):
        """文件不存在 → success=False"""
        mock_file = MagicMock()
        mock_file.exists.return_value = False

        svc = CreateDatasetService(dataset_repo=MagicMock(), file_repo=mock_file)
        resp = svc.execute(
            CreateDatasetRequest(
                owner_id=1, name="x", file_path="/missing.csv"
            )
        )

        assert resp.success is False
        assert "not found" in resp.error

    def test_unsupported_format(self):
        """不支持的文件格式 → success=False"""
        mock_file = MagicMock()
        mock_file.get_file_ext.return_value = ".txt"
        mock_file.exists.return_value = True

        svc = CreateDatasetService(dataset_repo=MagicMock(), file_repo=mock_file)
        resp = svc.execute(
            CreateDatasetRequest(
                owner_id=1, name="x", file_path="/bad.txt"
            )
        )

        assert resp.success is False
        assert "Unsupported" in resp.error


class TestGetDatasetsService:
    """GetDatasetsService 单元测试"""

    def test_get_all_empty(self):
        """空列表 → items=[] total=0"""
        mock_repo = MagicMock()
        mock_repo.find_all.return_value = []

        svc = GetDatasetsService(dataset_repo=mock_repo)
        resp = svc.get_all(owner_id=1)

        assert resp.items == []
        assert resp.total == 0
        assert resp.error is None

    def test_get_all_with_data(self):
        """有数据 → 只返回匹配 owner_id 的"""
        ds1 = _make_dataset(owner_id=1, name="my_ds", id=1)
        ds2 = _make_dataset(owner_id=2, name="other_ds", id=2)
        mock_repo = MagicMock()
        mock_repo.find_all.return_value = [ds1, ds2]

        svc = GetDatasetsService(dataset_repo=mock_repo)
        resp = svc.get_all(owner_id=1)

        assert resp.total == 1
        assert resp.items[0].name == "my_ds"

    def test_get_by_id_found(self):
        """匹配 owner → 返回 dataset"""
        ds = _make_dataset(owner_id=1, id=1, name="myds")
        mock_repo = MagicMock()
        mock_repo.find.return_value = ds

        svc = GetDatasetsService(dataset_repo=mock_repo)
        resp = svc.get_by_id(1, owner_id=1)

        assert resp.dataset is not None
        assert resp.dataset.name == "myds"
        assert resp.error is None

    def test_get_by_id_not_found(self):
        """不存在 → 返回 error"""
        mock_repo = MagicMock()
        mock_repo.find.return_value = None

        svc = GetDatasetsService(dataset_repo=mock_repo)
        resp = svc.get_by_id(999, owner_id=1)

        assert resp.dataset is None
        assert "not found" in resp.error

    def test_get_by_id_wrong_owner(self):
        """owner 不匹配 → Access denied"""
        ds = _make_dataset(owner_id=2, id=1, name="other")
        mock_repo = MagicMock()
        mock_repo.find.return_value = ds

        svc = GetDatasetsService(dataset_repo=mock_repo)
        resp = svc.get_by_id(1, owner_id=1)

        assert resp.dataset is None
        assert "Access denied" in resp.error
