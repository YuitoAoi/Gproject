"""DatasetProcessService 样本读取测试"""
import uuid
from unittest.mock import MagicMock, patch

import pytest

from src.core.dataset import DatasetMeta
from src.services.dataset_process_service import (
    DatasetProcessService,
    SampleRequest,
)


@pytest.fixture
def svc():
    return DatasetProcessService(MagicMock(), MagicMock(), MagicMock())


class TestSampleParsing:

    def test_jsonl_sample(self, svc):
        jsonl_data = b'{"text":"hello","label":"a"}\n{"text":"world","label":"b"}\n'
        ds = MagicMock()
        ds.meta = DatasetMeta(format="json", file_path="/t.jsonl", file_size=100)
        svc._dataset_repo.find_by_id.return_value = ds
        svc._file_repo.exists.return_value = True
        svc._file_repo.read.return_value = jsonl_data

        resp = svc.get_sample(SampleRequest(dataset_id=uuid.uuid4(), limit=10))
        assert len(resp.rows) == 2
        assert "text" in resp.columns

    @patch("src.services.dataset_process_service.io")
    def test_xlsx_sample(self, mock_io, svc):
        ds = MagicMock()
        ds.meta = DatasetMeta(format="xlsx", file_path="/t.xlsx", file_size=100)
        svc._dataset_repo.find_by_id.return_value = ds
        svc._file_repo.exists.return_value = True
        svc._file_repo.read.return_value = b"xlsx_bytes"

        mock_wb = MagicMock()
        mock_ws = MagicMock()
        mock_wb.active = mock_ws
        mock_ws.iter_rows.return_value = iter([("A", "B"), (1, 2)])

        with patch("openpyxl.load_workbook", return_value=mock_wb):
            resp = svc.get_sample(SampleRequest(dataset_id=uuid.uuid4(), limit=10))
            assert resp.columns == ["A", "B"]

    def test_csv_empty(self, svc):
        ds = MagicMock()
        ds.meta = DatasetMeta(format="csv", file_path="/t.csv", file_size=0)
        svc._dataset_repo.find_by_id.return_value = ds
        svc._file_repo.exists.return_value = True
        svc._file_repo.read.return_value = b""

        resp = svc.get_sample(SampleRequest(dataset_id=uuid.uuid4(), limit=10))
        assert resp.columns == []
        assert resp.rows == []
