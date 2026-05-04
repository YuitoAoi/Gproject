"""DatasetTagService 集成测试"""
import pytest

from src.db_connections.sqlite import SqliteConnection
from src.adapters.repositories.dataset_tag_repo import DatasetTagRepositoryAdapter
from src.services.dataset_tag_service import (
    DatasetTagCreateRequest,
    DatasetTagDeleteRequest,
    DatasetTagInfoGetRequest,
    DatasetTagUpdateRequest,
    DatasetTagService,
)
from src.services.interfaces.dataset_repository import DatasetRepository


class _FakeDatasetRepo(DatasetRepository):
    """桩：tag service 删除时需要查数据集引用"""
    def find(self, id): pass
    def find_by_owner(self, owner_id): return []
    def find_all(self): pass
    def create(self, ds): pass
    def exists(self, id): return False
    def update(self, id, ds): pass
    def remove(self, id): pass
    def remove_batch(self, ids): pass


@pytest.fixture(scope="session")
def tag_svc_conn():
    conn = SqliteConnection("sqlite:///:memory:", echo=False)
    conn.start()
    DatasetTagRepositoryAdapter(conn).init_table()
    yield conn
    conn.dispose()


@pytest.fixture
def tag_svc(tag_svc_conn):
    from sqlalchemy import text
    with tag_svc_conn.new_session() as s:
        s.execute(text("DELETE FROM dataset_tags"))
        s.commit()
    repo = DatasetTagRepositoryAdapter(tag_svc_conn)
    return DatasetTagService(repo, _FakeDatasetRepo())


class TestTagService:

    def test_create_tag(self, tag_svc):
        req = DatasetTagCreateRequest(name="red", color="#f00", desc="warm")
        resp = tag_svc.create_tag(req, owner_id=1)
        assert resp.success is True

    def test_create_duplicate(self, tag_svc):
        tag_svc.create_tag(DatasetTagCreateRequest(name="dup", color="#111"), owner_id=1)
        resp = tag_svc.create_tag(DatasetTagCreateRequest(name="dup", color="#222"), owner_id=1)
        assert resp.success is False
        assert "already exists" in resp.error

    def test_get_tag(self, tag_svc):
        r = tag_svc.create_tag(DatasetTagCreateRequest(name="blue"), owner_id=1)
        tags = tag_svc.get_tags(owner_id=1)
        tag_id = tags.tags[0].tag_id

        resp = tag_svc.get_tag(owner_id=1, tag_id=tag_id)
        assert resp.success is True
        assert resp.tag_name == "blue"

    def test_get_tag_not_found(self, tag_svc):
        resp = tag_svc.get_tag(owner_id=1, tag_id=999)
        assert resp.success is False
        assert "not found" in resp.error

    def test_get_tag_wrong_owner(self, tag_svc):
        r = tag_svc.create_tag(DatasetTagCreateRequest(name="secret"), owner_id=2)
        tags = tag_svc.get_tags(owner_id=2)
        tag_id = tags.tags[0].tag_id

        resp = tag_svc.get_tag(owner_id=1, tag_id=tag_id)
        assert resp.success is False

    def test_get_tags(self, tag_svc):
        tag_svc.create_tag(DatasetTagCreateRequest(name="a"), owner_id=1)
        tag_svc.create_tag(DatasetTagCreateRequest(name="b"), owner_id=1)
        tag_svc.create_tag(DatasetTagCreateRequest(name="c"), owner_id=2)

        resp = tag_svc.get_tags(owner_id=1)
        assert resp.success is True
        assert len(resp.tags) == 2

    def test_get_tags_empty(self, tag_svc):
        resp = tag_svc.get_tags(owner_id=1)
        assert resp.success is True
        assert resp.tags == []

    def test_update_tag(self, tag_svc):
        r = tag_svc.create_tag(DatasetTagCreateRequest(name="old"), owner_id=1)
        tags = tag_svc.get_tags(owner_id=1)
        tag_id = tags.tags[0].tag_id

        req = DatasetTagUpdateRequest(tag_id=tag_id, tag_name="new", tag_color="#fff")
        resp = tag_svc.update_tag(req, owner_id=1)
        assert resp.success is True

        info = tag_svc.get_tag(owner_id=1, tag_id=tag_id)
        assert info.tag_name == "new"
        assert info.tag_color == "#fff"

    def test_update_tag_not_found(self, tag_svc):
        req = DatasetTagUpdateRequest(tag_id=999, tag_name="ghost")
        resp = tag_svc.update_tag(req, owner_id=1)
        assert resp.success is False

    def test_update_tag_wrong_owner(self, tag_svc):
        r = tag_svc.create_tag(DatasetTagCreateRequest(name="owned"), owner_id=2)
        tags = tag_svc.get_tags(owner_id=2)
        tag_id = tags.tags[0].tag_id

        req = DatasetTagUpdateRequest(tag_id=tag_id, tag_name="hack")
        resp = tag_svc.update_tag(req, owner_id=1)
        assert resp.success is False

    def test_update_tag_duplicate_name(self, tag_svc):
        tag_svc.create_tag(DatasetTagCreateRequest(name="first"), owner_id=1)
        tag_svc.create_tag(DatasetTagCreateRequest(name="second"), owner_id=1)
        tags = tag_svc.get_tags(owner_id=1)
        second_id = [t for t in tags.tags if t.tag_name == "second"][0].tag_id

        req = DatasetTagUpdateRequest(tag_id=second_id, tag_name="first")
        resp = tag_svc.update_tag(req, owner_id=1)
        assert resp.success is False

    def test_delete_tag_force(self, tag_svc):
        r = tag_svc.create_tag(DatasetTagCreateRequest(name="temp"), owner_id=1)
        tags = tag_svc.get_tags(owner_id=1)
        tag_id = tags.tags[0].tag_id

        resp = tag_svc.delete_tag(owner_id=1, tag_id=tag_id, force=True)
        assert resp.success is True

        info = tag_svc.get_tag(owner_id=1, tag_id=tag_id)
        assert info.success is False

    def test_delete_tag_not_found(self, tag_svc):
        resp = tag_svc.delete_tag(owner_id=1, tag_id=999)
        assert resp.success is False

    def test_delete_tag_wrong_owner(self, tag_svc):
        r = tag_svc.create_tag(DatasetTagCreateRequest(name="mine"), owner_id=2)
        tags = tag_svc.get_tags(owner_id=2)
        tag_id = tags.tags[0].tag_id

        resp = tag_svc.delete_tag(owner_id=1, tag_id=tag_id)
        assert resp.success is False
