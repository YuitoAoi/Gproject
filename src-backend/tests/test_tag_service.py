"""DatasetTagService 集成测试"""

import uuid as _uuid
import pytest

_O1 = _uuid.uuid4()
_O2 = _uuid.uuid4()

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
    """桩：可预设数据集列表，用于测试 tag 删除时的级联行为"""

    def __init__(self, datasets=None):
        self._datasets = datasets or []
        self.updates = []  # 记录 update 调用
        self.deletes = []  # 记录 remove 调用

    def find_by_id(self, id):
        for d in self._datasets:
            if d.id == id:
                return d
        return None

    def find_by_owner(self, owner_id):
        return [d for d in self._datasets if d.owner_id == owner_id]

    def find_all(self):
        return self._datasets

    def create(self, dataset):
        pass

    def exists(self, id):
        return any(d.id == id for d in self._datasets)

    def update(self, id, dataset):
        self.updates.append((id, dataset))
        return None

    def remove(self, id):
        self.deletes.append(id)
        return None

    def remove_batch(self, ids):
        return []


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


@pytest.fixture
def tag_svc_with_datasets(tag_svc_conn):
    """带预设数据集的 tag service，用于测试 force 级联删除。"""
    from datetime import datetime
    from src.core.dataset import Dataset, DatasetMeta
    from sqlalchemy import text

    with tag_svc_conn.new_session() as s:
        s.execute(text("DELETE FROM dataset_tags"))
        s.commit()

    now = datetime.now()
    _ds1_id = _uuid.uuid4()
    _ds2_id = _uuid.uuid4()
    _owner = _uuid.uuid4()
    _tag_a = _uuid.uuid4()
    _tag_b = _uuid.uuid4()
    ds1 = Dataset(
        id=_ds1_id,
        owner_id=_owner,
        name="ds_one",
        meta=DatasetMeta(format="csv", file_path="/a.csv", file_size=10),
        created_at=now,
        updated_at=now,
        tag_ids=[_tag_a],
    )
    ds2 = Dataset(
        id=_ds2_id,
        owner_id=_owner,
        name="ds_two",
        meta=DatasetMeta(format="csv", file_path="/b.csv", file_size=20),
        created_at=now,
        updated_at=now,
        tag_ids=[_tag_a, _tag_b],
    )
    fake_ds_repo = _FakeDatasetRepo([ds1, ds2])
    tag_repo = DatasetTagRepositoryAdapter(tag_svc_conn)
    return DatasetTagService(tag_repo, fake_ds_repo), fake_ds_repo


class TestTagService:

    def test_create_tag(self, tag_svc):
        req = DatasetTagCreateRequest(name="red", color="#ff0000", desc="warm")
        resp = tag_svc.create_tag(req, owner_id=_O1)
        assert resp.success is True

    def test_create_duplicate(self, tag_svc):
        tag_svc.create_tag(
            DatasetTagCreateRequest(name="dup", color="#111111"), owner_id=_O1
        )
        resp = tag_svc.create_tag(
            DatasetTagCreateRequest(name="dup", color="#222222"), owner_id=_O1
        )
        assert resp.success is False
        assert "already exists" in resp.error

    def test_get_tag(self, tag_svc):
        r = tag_svc.create_tag(DatasetTagCreateRequest(name="blue"), owner_id=_O1)
        tags = tag_svc.get_tags(owner_id=_O1)
        tag_id = tags.tags[0].tag_id

        resp = tag_svc.get_tag(owner_id=_O1, tag_id=tag_id)
        assert resp.success is True
        assert resp.tag_name == "blue"

    def test_get_tag_not_found(self, tag_svc):
        resp = tag_svc.get_tag(owner_id=_O1, tag_id=999)
        assert resp.success is False
        assert "not found" in resp.error

    def test_get_tag_wrong_owner(self, tag_svc):
        r = tag_svc.create_tag(DatasetTagCreateRequest(name="secret"), owner_id=_O1)
        tags = tag_svc.get_tags(owner_id=_O1)
        tag_id = tags.tags[0].tag_id

        resp = tag_svc.get_tag(owner_id=_O2, tag_id=tag_id)
        assert resp.success is False

    def test_get_tags(self, tag_svc):
        tag_svc.create_tag(DatasetTagCreateRequest(name="a"), owner_id=_O1)
        tag_svc.create_tag(DatasetTagCreateRequest(name="b"), owner_id=_O1)
        tag_svc.create_tag(DatasetTagCreateRequest(name="c"), owner_id=_O1)

        resp = tag_svc.get_tags(owner_id=_O1)
        assert resp.success is True
        assert len(resp.tags) == 2

    def test_get_tags_empty(self, tag_svc):
        resp = tag_svc.get_tags(owner_id=_O1)
        assert resp.success is True
        assert resp.tags == []

    def test_update_tag(self, tag_svc):
        r = tag_svc.create_tag(DatasetTagCreateRequest(name="old"), owner_id=_O1)
        tags = tag_svc.get_tags(owner_id=_O1)
        tag_id = tags.tags[0].tag_id

        req = DatasetTagUpdateRequest(tag_id=tag_id, tag_name="new", tag_color="#fff")
        resp = tag_svc.update_tag(req, owner_id=_O1)
        assert resp.success is True

        info = tag_svc.get_tag(owner_id=_O1, tag_id=tag_id)
        assert info.tag_name == "new"
        assert info.tag_color == "#fff"

    def test_update_tag_not_found(self, tag_svc):
        req = DatasetTagUpdateRequest(tag_id=999, tag_name="ghost")
        resp = tag_svc.update_tag(req, owner_id=_O1)
        assert resp.success is False

    def test_update_tag_wrong_owner(self, tag_svc):
        r = tag_svc.create_tag(DatasetTagCreateRequest(name="owned"), owner_id=_O1)
        tags = tag_svc.get_tags(owner_id=_O1)
        tag_id = tags.tags[0].tag_id

        req = DatasetTagUpdateRequest(tag_id=tag_id, tag_name="hack")
        resp = tag_svc.update_tag(req, owner_id=_O1)
        assert resp.success is False

    def test_update_tag_duplicate_name(self, tag_svc):
        tag_svc.create_tag(DatasetTagCreateRequest(name="first"), owner_id=_O1)
        tag_svc.create_tag(DatasetTagCreateRequest(name="second"), owner_id=_O1)
        tags = tag_svc.get_tags(owner_id=_O1)
        second_id = [t for t in tags.tags if t.tag_name == "second"][0].tag_id

        req = DatasetTagUpdateRequest(tag_id=second_id, tag_name="first")
        resp = tag_svc.update_tag(req, owner_id=_O1)
        assert resp.success is False

    def test_delete_tag_force(self, tag_svc):
        r = tag_svc.create_tag(DatasetTagCreateRequest(name="temp"), owner_id=_O1)
        tags = tag_svc.get_tags(owner_id=_O1)
        tag_id = tags.tags[0].tag_id

        resp = tag_svc.delete_tag(owner_id=_O1, tag_id=tag_id, force=True)
        assert resp.success is True

        info = tag_svc.get_tag(owner_id=_O1, tag_id=tag_id)
        assert info.success is False

    def test_delete_tag_not_found(self, tag_svc):
        resp = tag_svc.delete_tag(owner_id=_O1, tag_id=999)
        assert resp.success is False

    def test_delete_tag_wrong_owner(self, tag_svc):
        r = tag_svc.create_tag(DatasetTagCreateRequest(name="mine"), owner_id=_O1)
        tags = tag_svc.get_tags(owner_id=_O1)
        tag_id = tags.tags[0].tag_id

        resp = tag_svc.delete_tag(owner_id=_O1, tag_id=tag_id)
        assert resp.success is False

    # ── force 级联删除 ─────────────────────────────────────

    def test_delete_force_cascade(self, tag_svc_with_datasets):
        """force=True 时：从引用该 tag 的所有数据集中移除 tag_id，然后删除标签"""
        svc, fake_ds = tag_svc_with_datasets
        # 创建 tag_id=99 的标签
        svc.create_tag(
            DatasetTagCreateRequest(name="cascade_target", color="#111111"),
            owner_id=_O1,
        )
        tags = svc.get_tags(owner_id=_O1)
        tag_id = tags.tags[0].tag_id  # real tag id from DB

        # force 删除 —— fake_ds 中有 ds1(tag_ids=[99]) 和 ds2(tag_ids=[99,100])
        # 但 real tag_id != 99，所以不会有级联。我们需要把 fake_ds 中的 tag_ids 换成真实的 tag_id
        # 重置 fake_ds 使用真实 tag_id
        from datetime import datetime
        from src.core.dataset import Dataset, DatasetMeta

        now = datetime.now()
        fake_ds._datasets = [
            Dataset(
                id=_uuid.uuid4(),
                owner_id=_O1,
                name="ds_one",
                meta=DatasetMeta(format="csv", file_path="/a.csv", file_size=10),
                status=0,
                tag_ids=[tag_id],
                created_at=now,
                updated_at=now,
            ),
            Dataset(
                id=_uuid.uuid4(),
                owner_id=_O1,
                name="ds_two",
                meta=DatasetMeta(format="csv", file_path="/b.csv", file_size=20),
                status=0,
                tag_ids=[tag_id, _uuid.uuid4()],
                created_at=now,
                updated_at=now,
            ),
        ]

        resp = svc.delete_tag(owner_id=_O1, tag_id=tag_id, force=True)
        assert resp.success is True

        # 验证：ds1.tag_ids 中不再包含该 tag_id
        updated_ds1 = fake_ds.find(fake_ds._datasets[0].id)
        assert tag_id not in updated_ds1.tag_ids
        # 验证：ds2.tag_ids 中不再包含该 tag_id
        updated_ds2 = fake_ds.find(fake_ds._datasets[1].id)
        assert tag_id not in updated_ds2.tag_ids

        # 验证：标签本身已删除
        info = svc.get_tag(owner_id=_O1, tag_id=tag_id)
        assert info.success is False

    def test_delete_force_false_with_refs(self, tag_svc_with_datasets):
        """force=False 且标签被数据集引用时，返回错误不删除"""
        svc, fake_ds = tag_svc_with_datasets
        svc.create_tag(
            DatasetTagCreateRequest(name="referenced", color="#ff0000"), owner_id=_O1
        )
        tags = svc.get_tags(owner_id=_O1)
        tag_id = tags.tags[0].tag_id

        from datetime import datetime
        from src.core.dataset import Dataset, DatasetMeta

        now = datetime.now()
        fake_ds._datasets = [
            Dataset(
                id=_uuid.uuid4(),
                owner_id=_O1,
                name="uses_tag",
                meta=DatasetMeta(format="csv", file_path="/a.csv", file_size=10),
                status=0,
                tag_ids=[tag_id],
                created_at=now,
                updated_at=now,
            ),
        ]

        resp = svc.delete_tag(owner_id=_O1, tag_id=tag_id, force=False)
        assert resp.success is False
        assert "uses_tag" in resp.error  # 错误信息应包含引用它的数据集名称

        # 验证：标签仍然存在
        info = svc.get_tag(owner_id=_O1, tag_id=tag_id)
        assert info.success is True
