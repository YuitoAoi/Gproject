"""Dataset 服务层集成测试（基于 SQLite 内存数据库）"""
from datetime import datetime
from pathlib import Path
from typing import Optional

import pytest

from src.core.config import config
from src.core.dataset import Dataset, DatasetMeta
from src.db_connections.sqlite import SqliteConnection
from src.adapters.repositories.dataset_repo import DatasetRepositoryAdapter
from src.services.dataset_import_export_service import (
    DatasetImportExportService,
    DatasetImportRequest,
    DatasetDownloadRequest,
    DatasetImportExportResponse,
)
from src.services.dataset_remove_service import (
    DatasetRemoveService,
    DatasetRemoveRequest,
    DatasetRemoveResponse,
)
from src.services.dataset_update_service import (
    DatasetUpdateService,
    DatasetUpdateRequest,
    DatasetUpdateResponse,
)
from src.services.dataset_get_service import GetDatasetsService
from src.services.interfaces.file_repository import FileRepository


# ══════════════════════════════════════════════════════════
# 内存文件仓库（测试用桩）
# ══════════════════════════════════════════════════════════

class _MemoryFileRepo(FileRepository):
    """内存文件仓库，通过 dict 模拟文件系统。"""

    def __init__(self, files: Optional[dict] = None):
        self._files: dict[str, bytes] = files or {}
        self._dirs: set[str] = set()

    def _touch(self, path: str, data: bytes = b""):
        self._files[path] = data

    # ── 实现必须的抽象方法 ──────────────────────────────

    def exists(self, url: str) -> bool:
        return url in self._files

    def read(self, url: str) -> bytes:
        if url not in self._files:
            raise FileNotFoundError(url)
        return self._files[url]

    def get_size(self, url: str) -> int:
        return len(self._files.get(url, b""))

    def get_file_ext(self, url: str) -> str:
        return Path(url).suffix

    def delete(self, url: str) -> bool:
        if url in self._files:
            del self._files[url]
            return True
        return False

    def copy(self, from_path: str, to_path: str) -> None:
        if from_path in self._files:
            self._files[to_path] = self._files[from_path]

    def write(self, url: str, data: bytes) -> None:
        if url in self._files:
            raise FileExistsError(url)
        self._files[url] = data

    def over_write(self, url: str, data: bytes) -> None:
        self._files[url] = data

    def create(self, path: str) -> None:
        self._files[path] = b""

    def move(self, from_path: str, to_path: str) -> None:
        if from_path in self._files:
            self._files[to_path] = self._files.pop(from_path)

    def rename(self, from_path: str, to_path: str) -> None:
        self.move(from_path, to_path)

    def read_chunk(self, url: str, offset: int, size: int) -> bytes:
        return self._files.get(url, b"")[offset:offset + size]

    def write_chunk(self, url: str, offset: int, data: bytes) -> None:
        pass

    def size(self, url: str) -> int:
        return self.get_size(url)

    def makedirs(self, path: str) -> None:
        self._dirs.add(path)

    def is_dir(self, url: str) -> bool:
        return url in self._dirs

    def list_dir(self, url: str) -> list[str]:
        return list(self._files.keys())

    def delete_dir(self, url: str) -> bool:
        self._dirs.discard(url)
        return True


# ══════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def sqlite_conn():
    """会话级：创建 SQLite 内存数据库连接，建表。"""
    conn = SqliteConnection("sqlite:///:memory:", echo=False)
    conn.start()

    repo = DatasetRepositoryAdapter(conn)
    repo.init_table()

    yield conn
    conn.dispose()


@pytest.fixture
def repo(sqlite_conn):
    """函数级：每个测试前清空表，确保隔离。"""
    from sqlalchemy import text
    with sqlite_conn.new_session() as session:
        session.execute(text("DELETE FROM datasets"))
        session.commit()
    return DatasetRepositoryAdapter(sqlite_conn)


@pytest.fixture
def file_repo(tmp_path):
    """函数级：使用真实临时目录 + FileRepository 桩。"""
    csv = tmp_path / "test.csv"
    csv.write_text("name,age\nAlice,30\nBob,25\n", encoding="utf-8")
    json_file = tmp_path / "test.json"
    json_file.write_text('[{"text":"hello"}]', encoding="utf-8")
    txt_file = tmp_path / "bad.txt"
    txt_file.write_text("hello")

    fr = _MemoryFileRepo()
    fr._touch(str(csv), csv.read_bytes())
    fr._touch(str(json_file), json_file.read_bytes())
    fr._touch(str(txt_file), txt_file.read_bytes())

    # 更新默认 meta 路径
    global _TEST_DIR
    _TEST_DIR = str(tmp_path)
    return fr


@pytest.fixture
def import_export_svc(repo, file_repo):
    return DatasetImportExportService(repo, file_repo)


@pytest.fixture
def remove_svc(repo, file_repo):
    return DatasetRemoveService(repo, file_repo)


@pytest.fixture
def update_svc(repo):
    return DatasetUpdateService(repo)


@pytest.fixture
def get_svc(repo):
    return GetDatasetsService(repo)


# ══════════════════════════════════════════════════════════
# 工具
# ══════════════════════════════════════════════════════════

_TEST_DIR = str(Path(__file__).parent / "_test_files")


def _make_meta(format="csv", file_path=None, file_size=28):
    if file_path is None:
        file_path = Path(_TEST_DIR) / "test.csv"
    return DatasetMeta(format=format, file_path=str(file_path), file_size=file_size)


def _import_csv(import_export_svc, owner_id=1, name="test_ds") -> DatasetImportExportResponse:
    """快捷导入一个 CSV 数据集。"""
    req = DatasetImportRequest(
        name=name,
        desc="test dataset",
        file_path=str(Path(_TEST_DIR) / "test.csv"),
    )
    return import_export_svc.import_dataset(req, owner_id)


# ══════════════════════════════════════════════════════════
# DatasetRepositoryAdapter 集成测试
# ══════════════════════════════════════════════════════════

class TestDatasetRepositoryAdapter:
    """DatasetRepositoryAdapter 基础 CRUD"""

    def test_create_returns_none_on_success(self, repo):
        ds = Dataset.new(owner_id=1, name="test", meta=_make_meta())
        err = repo.create(ds)
        assert err is None
        assert ds.id is not None
        assert ds.id > 0

    def test_find_returns_dataset(self, repo):
        ds = Dataset.new(owner_id=1, name="test", meta=_make_meta())
        repo.create(ds)
        found = repo.find(ds.id)
        assert found is not None
        assert found.name == "test"
        assert found.owner_id == 1

    def test_find_not_found(self, repo):
        assert repo.find(999) is None

    def test_find_by_owner(self, repo):
        repo.create(Dataset.new(owner_id=1, name="ds1", meta=_make_meta()))
        repo.create(Dataset.new(owner_id=1, name="ds2", meta=_make_meta()))
        repo.create(Dataset.new(owner_id=2, name="other", meta=_make_meta()))

        result = repo.find_by_owner(1)
        assert len(result) == 2
        assert all(d.owner_id == 1 for d in result)

    def test_find_all(self, repo):
        repo.create(Dataset.new(owner_id=1, name="a", meta=_make_meta()))
        repo.create(Dataset.new(owner_id=2, name="b", meta=_make_meta()))
        assert len(repo.find_all()) == 2

    def test_exists(self, repo):
        ds = Dataset.new(owner_id=1, name="x", meta=_make_meta())
        repo.create(ds)
        assert repo.exists(ds.id) is True
        assert repo.exists(999) is False

    def test_update_success(self, repo):
        ds = Dataset.new(owner_id=1, name="old", meta=_make_meta())
        repo.create(ds)
        ds.name = "new_name"
        err = repo.update(ds.id, ds)
        assert err is None

        refetched = repo.find(ds.id)
        assert refetched.name == "new_name"

    def test_update_not_found(self, repo):
        ds = Dataset.new(owner_id=1, name="ghost", meta=_make_meta())
        ds.id = 999
        err = repo.update(999, ds)
        assert isinstance(err, ValueError)

    def test_remove_success(self, repo):
        ds = Dataset.new(owner_id=1, name="to_delete", meta=_make_meta())
        repo.create(ds)
        err = repo.remove(ds.id)
        assert err is None
        assert repo.exists(ds.id) is False

    def test_remove_not_found(self, repo):
        err = repo.remove(999)
        assert isinstance(err, ValueError)

    def test_remove_batch(self, repo):
        ds1 = Dataset.new(owner_id=1, name="a", meta=_make_meta())
        ds2 = Dataset.new(owner_id=1, name="b", meta=_make_meta())
        repo.create(ds1)
        repo.create(ds2)
        repo.create(Dataset.new(owner_id=1, name="c", meta=_make_meta()))

        err = repo.remove_batch([ds1.id, ds2.id])
        assert err is None
        assert repo.exists(ds1.id) is False
        assert repo.exists(ds2.id) is False
        assert len(repo.find_all()) == 1

    def test_remove_batch_empty(self, repo):
        assert repo.remove_batch([]) is None

    def test_indexes_created(self, repo):
        """ensure_indexes / drop_indexes 幂等调用无误"""
        repo.ensure_indexes()
        repo.ensure_indexes()  # 重复调用不抛异常
        repo.drop_indexes()
        repo.drop_indexes()   # 重复删除不抛异常
        repo.ensure_indexes()  # 重新创建


# ══════════════════════════════════════════════════════════
# DatasetImportExportService 集成测试
# ══════════════════════════════════════════════════════════

class TestDatasetImportExportService:

    def test_import_csv_success(self, import_export_svc):
        import hashlib
        resp = _import_csv(import_export_svc)
        assert resp.success is True
        assert resp.dataset_id is not None
        assert resp.format == "csv"
        # 从实际文件内容计算预期哈希
        csv_path = Path(_TEST_DIR) / "test.csv"
        expected_hash = hashlib.sha256(csv_path.read_bytes()).hexdigest()
        assert resp.sha256 == expected_hash
        assert resp.file_size == csv_path.stat().st_size

    def test_import_file_not_found(self, import_export_svc):
        req = DatasetImportRequest(name="x", file_path=str(Path(_TEST_DIR) / "nope.csv"))
        resp = import_export_svc.import_dataset(req, 1)
        assert resp.success is False
        assert "not found" in resp.error

    def test_import_unsupported_format(self, import_export_svc, file_repo):
        bad = str(Path(_TEST_DIR) / "bad.txt")
        req = DatasetImportRequest(name="x", file_path=bad)
        resp = import_export_svc.import_dataset(req, 1)
        assert resp.success is False
        assert "Unsupported" in resp.error

    def test_import_rollback_on_error(self, import_export_svc, repo):
        """导入失败不应残留 DB 记录"""
        req = DatasetImportRequest(name="x", file_path=str(Path(_TEST_DIR) / "nope.csv"))
        import_export_svc.import_dataset(req, 1)
        assert len(repo.find_all()) == 0

    def test_download_success(self, import_export_svc):
        resp = _import_csv(import_export_svc)
        dl_req = DatasetDownloadRequest(dataset_id=resp.dataset_id)
        dl = import_export_svc.download(dl_req)
        assert dl.success is True
        import hashlib
        csv_path = Path(_TEST_DIR) / "test.csv"
        expected_hash = hashlib.sha256(csv_path.read_bytes()).hexdigest()
        assert dl.sha256 == expected_hash
        assert dl.file_size == csv_path.stat().st_size
        assert dl.filename.endswith(".csv")

    def test_download_not_found(self, import_export_svc):
        req = DatasetDownloadRequest(dataset_id=999)
        resp = import_export_svc.download(req)
        assert resp.success is False
        assert "not found" in resp.error

    def test_import_with_tags(self, import_export_svc):
        req = DatasetImportRequest(
            name="tagged", file_path=str(Path(_TEST_DIR) / "test.csv"), tag_ids=[1, 2, 3],
        )
        resp = import_export_svc.import_dataset(req, 1)
        assert resp.success is True


# ══════════════════════════════════════════════════════════
# DatasetRemoveService 集成测试
# ══════════════════════════════════════════════════════════

class TestDatasetRemoveService:

    def test_remove_single(self, import_export_svc, remove_svc, repo):
        resp = _import_csv(import_export_svc, owner_id=1)
        req = DatasetRemoveRequest(dataset_ids=[resp.dataset_id])
        result = remove_svc.execute(req, owner_id=1)
        assert result.success is True
        assert resp.dataset_id in result.deleted
        assert repo.exists(resp.dataset_id) is False

    def test_remove_batch(self, import_export_svc, remove_svc, repo):
        r1 = _import_csv(import_export_svc, owner_id=1, name="a")
        r2 = _import_csv(import_export_svc, owner_id=1, name="b")
        req = DatasetRemoveRequest(dataset_ids=[r1.dataset_id, r2.dataset_id])
        result = remove_svc.execute(req, owner_id=1)
        assert result.success is True
        assert len(result.deleted) == 2

    def test_remove_wrong_owner(self, import_export_svc, remove_svc):
        resp = _import_csv(import_export_svc, owner_id=1)
        req = DatasetRemoveRequest(dataset_ids=[resp.dataset_id])
        result = remove_svc.execute(req, owner_id=2)
        assert result.success is False
        assert "does not belong" in result.errors[0]

    def test_remove_not_found(self, remove_svc):
        req = DatasetRemoveRequest(dataset_ids=[999])
        result = remove_svc.execute(req, owner_id=1)
        assert result.success is False
        assert "not found" in result.errors[0]


# ══════════════════════════════════════════════════════════
# DatasetUpdateService 集成测试
# ══════════════════════════════════════════════════════════

class TestDatasetUpdateService:

    def test_update_name(self, import_export_svc, update_svc, repo):
        resp = _import_csv(import_export_svc, owner_id=1, name="original")
        req = DatasetUpdateRequest(dataset_id=resp.dataset_id, name="renamed")
        result = update_svc.execute(req, owner_id=1)
        assert result.success is True

        ds = repo.find(resp.dataset_id)
        assert ds.name == "renamed"

    def test_update_desc_and_tags(self, import_export_svc, update_svc, repo):
        resp = _import_csv(import_export_svc, owner_id=1)
        req = DatasetUpdateRequest(
            dataset_id=resp.dataset_id, desc="new desc", tag_ids=[10, 20],
        )
        result = update_svc.execute(req, owner_id=1)
        assert result.success is True

        ds = repo.find(resp.dataset_id)
        assert ds.desc == "new desc"
        assert ds.tag_ids == [10, 20]

    def test_update_wrong_owner(self, import_export_svc, update_svc):
        resp = _import_csv(import_export_svc, owner_id=1)
        req = DatasetUpdateRequest(dataset_id=resp.dataset_id, name="hack")
        result = update_svc.execute(req, owner_id=2)
        assert result.success is False
        assert "not found" in result.error

    def test_update_no_changes(self, import_export_svc, update_svc):
        resp = _import_csv(import_export_svc, owner_id=1)
        req = DatasetUpdateRequest(dataset_id=resp.dataset_id)
        result = update_svc.execute(req, owner_id=1)
        assert result.success is True


# ══════════════════════════════════════════════════════════
# GetDatasetsService 集成测试
# ══════════════════════════════════════════════════════════

class TestGetDatasetsService:

    def test_get_all_filters_by_owner(self, import_export_svc, get_svc):
        _import_csv(import_export_svc, owner_id=1, name="ds1")
        _import_csv(import_export_svc, owner_id=2, name="ds2")
        resp = get_svc.get_all(owner_id=1)
        assert resp.total == 1
        assert resp.items[0].name == "ds1"

    def test_get_by_id(self, import_export_svc, get_svc):
        r = _import_csv(import_export_svc, owner_id=1, name="target")
        resp = get_svc.get_by_id(r.dataset_id, owner_id=1)
        assert resp.dataset is not None
        assert resp.dataset.name == "target"

    def test_get_by_id_wrong_owner(self, import_export_svc, get_svc):
        r = _import_csv(import_export_svc, owner_id=1)
        resp = get_svc.get_by_id(r.dataset_id, owner_id=2)
        assert resp.dataset is None
        assert "Access denied" in resp.error
