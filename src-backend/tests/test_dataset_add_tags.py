# ruff: noqa: RUF002, RUF003, E402
"""DatasetAddTagsBatchService 测试 —— 单元测试 + 集成测试"""

from unittest.mock import MagicMock

import pytest
from src.core.dataset import Dataset, DatasetMeta
from src.services.dataset_update_service import (
    DatasetAddTagsBatchRequest,
    DatasetAddTagsBatchService,
)


def _make_dataset(owner_id=1, id=1, name="ds1", tag_ids=None):
    from datetime import datetime

    now = datetime.now()
    return Dataset(
        id=id,
        owner_id=owner_id,
        name=name,
        meta=DatasetMeta(format="csv", file_path="/d.csv", file_size=100),
        status=0,
        tag_ids=tag_ids or [],
        created_at=now,
        updated_at=now,
    )


# ══════════════════════════════════════════════════════════
# 单元测试（mock 仓储）
# ══════════════════════════════════════════════════════════


class TestAddTagsBatchUnit:
    @pytest.fixture
    def mock_repo(self):
        return MagicMock()

    @pytest.fixture
    def svc(self, mock_repo):
        return DatasetAddTagsBatchService(mock_repo)

    def test_success(self, svc, mock_repo):
        """正常：给多个数据集添加标签。"""
        ds1 = _make_dataset(id=1, owner_id=1, tag_ids=[])
        ds2 = _make_dataset(id=2, owner_id=1, tag_ids=[5])
        mock_repo.find_by_id.side_effect = [ds1, ds2]

        req = DatasetAddTagsBatchRequest(dataset_ids=[1, 2], tag_ids=[3, 7])
        resp = svc.execute(req, owner_id=1)

        assert resp.success is True
        assert mock_repo.update.call_count == 2
        # ds1 添加了 [3, 7]
        assert ds1.tag_ids == [3, 7]
        # ds2 已含 [5]，追加 [3, 7]
        assert ds2.tag_ids == [5, 3, 7]

    def test_empty_dataset_ids(self, svc):
        """空 dataset_ids 列表应返回错误。"""
        req = DatasetAddTagsBatchRequest(dataset_ids=[], tag_ids=[1])
        resp = svc.execute(req, owner_id=1)
        assert resp.success is False
        assert "dataset" in resp.error.lower()

    def test_empty_tag_ids(self, svc):
        """空 tag_ids 列表应返回错误。"""
        req = DatasetAddTagsBatchRequest(dataset_ids=[1], tag_ids=[])
        resp = svc.execute(req, owner_id=1)
        assert resp.success is False
        assert "tag" in resp.error.lower()

    def test_not_found(self, svc, mock_repo):
        """数据集不存在时记录错误但不阻塞其他。"""
        mock_repo.find_by_id.return_value = None

        req = DatasetAddTagsBatchRequest(dataset_ids=[1, 2], tag_ids=[3])
        resp = svc.execute(req, owner_id=1)

        assert resp.success is False
        assert "not found" in resp.error
        assert "1" in resp.error or "2" in resp.error
        assert mock_repo.update.call_count == 0

    def test_wrong_owner(self, svc, mock_repo):
        """数据集不属于当前用户时记录错误。"""
        ds = _make_dataset(id=1, owner_id=2)
        mock_repo.find_by_id.return_value = ds

        req = DatasetAddTagsBatchRequest(dataset_ids=[1], tag_ids=[3])
        resp = svc.execute(req, owner_id=1)

        assert resp.success is False
        assert "does not belong" in resp.error

    def test_dedup_skips_existing_tags(self, svc, mock_repo):
        """已存在的标签不重复添加，无变化时不调用 update。"""
        ds = _make_dataset(id=1, owner_id=1, tag_ids=[3, 7])
        mock_repo.find_by_id.return_value = ds

        req = DatasetAddTagsBatchRequest(dataset_ids=[1], tag_ids=[3, 7, 10])
        resp = svc.execute(req, owner_id=1)

        assert resp.success is True
        # 只有 new tag [10] 需要追加
        assert 10 in ds.tag_ids
        assert ds.tag_ids.count(3) == 1
        assert ds.tag_ids.count(7) == 1

    def test_partial_failure(self, svc, mock_repo):
        """部分成功部分失败：成功的不回滚，失败记录错误。"""
        ds1 = _make_dataset(id=1, owner_id=1)
        ds2 = _make_dataset(id=2, owner_id=1)
        ds3 = _make_dataset(id=3, owner_id=2)  # wrong owner

        def find_side_effect(id):
            return {1: ds1, 2: ds2, 3: ds3}.get(id)

        mock_repo.find_by_id.side_effect = find_side_effect

        req = DatasetAddTagsBatchRequest(dataset_ids=[1, 2, 3], tag_ids=[5])
        resp = svc.execute(req, owner_id=1)

        assert resp.success is False
        assert "does not belong" in resp.error
        # ds1, ds2 仍然成功
        assert ds1.tag_ids == [5]
        assert ds2.tag_ids == [5]
        assert mock_repo.update.call_count == 2

    def test_all_already_have_tags(self, svc, mock_repo):
        """所有数据集已包含全部请求标签时，不发 update 调用。"""
        ds = _make_dataset(id=1, owner_id=1, tag_ids=[3, 7])
        mock_repo.find_by_id.return_value = ds

        req = DatasetAddTagsBatchRequest(dataset_ids=[1], tag_ids=[3])
        resp = svc.execute(req, owner_id=1)

        assert resp.success is True
        assert mock_repo.update.call_count == 0

    def test_repo_update_failure_caught(self, svc, mock_repo):
        """仓储 update 抛异常时被捕获并记录错误。"""
        ds = _make_dataset(id=1, owner_id=1)
        mock_repo.find_by_id.return_value = ds
        mock_repo.update.side_effect = RuntimeError("DB crash")

        req = DatasetAddTagsBatchRequest(dataset_ids=[1], tag_ids=[5])
        resp = svc.execute(req, owner_id=1)

        assert resp.success is False
        assert "Failed to update" in resp.error


# ══════════════════════════════════════════════════════════
# 集成测试（SQLite 内存数据库）
# ══════════════════════════════════════════════════════════

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src" / "services"))


@pytest.fixture(scope="session")
def sqlite_conn():
    from src.db_connections.sqlite import SqliteConnection

    conn = SqliteConnection("sqlite:///:memory:", echo=False)
    conn.start()
    from src.adapters.repositories.dataset_repo import DatasetRepositoryAdapter

    DatasetRepositoryAdapter(conn).init_table()
    yield conn
    conn.dispose()


@pytest.fixture
def repo(sqlite_conn):
    from sqlalchemy import text

    with sqlite_conn.new_session() as s:
        s.execute(text("DELETE FROM datasets"))
        s.commit()
    from src.adapters.repositories.dataset_repo import DatasetRepositoryAdapter

    return DatasetRepositoryAdapter(sqlite_conn)


@pytest.fixture
def add_tags_svc(repo):
    return DatasetAddTagsBatchService(repo)


def _ds(owner_id=1, name="ds1", tag_ids=None) -> Dataset:
    from datetime import datetime

    now = datetime.now()
    return Dataset(
        owner_id=owner_id,
        name=name,
        meta=DatasetMeta(format="csv", file_path="/d.csv", file_size=100),
        status=0,
        tag_ids=tag_ids or [],
        created_at=now,
        updated_at=now,
    )


class TestAddTagsBatchIntegration:
    def test_add_tags_end_to_end(self, repo, add_tags_svc):
        """E2E：创建数据集 → 批量加标签 → DB 中验证。"""
        ds1 = _ds(name="a")
        ds2 = _ds(name="b")
        assert repo.create(ds1) is None
        assert repo.create(ds2) is None

        req = DatasetAddTagsBatchRequest(dataset_ids=[ds1.id, ds2.id], tag_ids=[10, 20])
        resp = add_tags_svc.execute(req, owner_id=1)
        assert resp.success is True

        # DB 验证
        r1 = repo.find_by_id(ds1.id)
        r2 = repo.find_by_id(ds2.id)
        assert r1.tag_ids == [10, 20]
        assert r2.tag_ids == [10, 20]

    def test_add_tags_append_to_existing(self, repo, add_tags_svc):
        """已有标签的数据集，新标签追加而非覆盖。"""
        ds = _ds(tag_ids=[1, 2])
        assert repo.create(ds) is None

        req = DatasetAddTagsBatchRequest(dataset_ids=[ds.id], tag_ids=[3, 4])
        resp = add_tags_svc.execute(req, owner_id=1)
        assert resp.success is True

        r = repo.find_by_id(ds.id)
        assert sorted(r.tag_ids) == [1, 2, 3, 4]

    def test_add_tags_dedup_integration(self, repo, add_tags_svc):
        """重复标签不会多次添加。"""
        ds = _ds(tag_ids=[5])
        assert repo.create(ds) is None

        req = DatasetAddTagsBatchRequest(dataset_ids=[ds.id], tag_ids=[5, 6])
        resp = add_tags_svc.execute(req, owner_id=1)
        assert resp.success is True

        r = repo.find_by_id(ds.id)
        assert sorted(r.tag_ids) == [5, 6]
        assert r.tag_ids.count(5) == 1

    def test_wrong_owner_fails_integration(self, repo, add_tags_svc):
        """跨用户添加标签被拒绝。"""
        ds = _ds(owner_id=2)
        assert repo.create(ds) is None

        req = DatasetAddTagsBatchRequest(dataset_ids=[ds.id], tag_ids=[1])
        resp = add_tags_svc.execute(req, owner_id=1)
        assert resp.success is False
        assert "does not belong" in resp.error
