"""DatasetTagRepositoryAdapter 集成测试"""
import uuid
from datetime import datetime

import pytest

from src.db_connections.sqlite import SqliteConnection
from src.adapters.repositories.dataset_tag_repo import DatasetTagRepositoryAdapter
from src.core.dataset_tag import DatasetTag


_OWNER = uuid.uuid4()
_OWNER2 = uuid.uuid4()


def _make_tag(name="red", color="#ff0000", desc="warm", owner=_OWNER) -> DatasetTag:
    return DatasetTag(
        id=uuid.uuid4(),
        owner_id=owner,
        name=name,
        color=color,
        description=desc,
        created_at=datetime.now(),
    )


@pytest.fixture(scope="session")
def tag_conn():
    conn = SqliteConnection("sqlite:///:memory:", echo=False)
    conn.start()

    repo = DatasetTagRepositoryAdapter(conn)
    repo.init_table()

    yield conn
    conn.dispose()


@pytest.fixture
def tag_repo(tag_conn):
    from sqlalchemy import text
    with tag_conn.new_session() as s:
        s.execute(text("DELETE FROM dataset_tags"))
        s.commit()
    return DatasetTagRepositoryAdapter(tag_conn)


class TestTagRepository:

    def test_create_success(self, tag_repo):
        tag = _make_tag()
        tag_repo.create(tag)
        found = tag_repo.find_by_name(_OWNER, "red")
        assert found is not None
        assert found.name == "red"

    def test_create_duplicate_name_same_owner(self, tag_repo):
        tag_repo.create(_make_tag(name="dup", color="#111111"))
        with pytest.raises(Exception):  # DB IntegrityError
            tag_repo.create(_make_tag(name="dup", color="#222222"))

    def test_create_same_name_diff_owner(self, tag_repo):
        tag_repo.create(_make_tag(name="shared", color="#333333", owner=_OWNER))
        tag_repo.create(_make_tag(name="shared", color="#444444", owner=_OWNER2))
        # 不抛异常即通过

    def test_find_by_id(self, tag_repo):
        tag = _make_tag(name="green", color="#00ff00")
        tag_repo.create(tag)
        found = tag_repo.find_by_id(tag.id)
        assert found is not None
        assert found.name == "green"
        assert found.color == "#00ff00"

    def test_find_by_id_not_found(self, tag_repo):
        assert tag_repo.find_by_id(uuid.uuid4()) is None

    def test_find_by_name(self, tag_repo):
        tag = _make_tag(name="blue", color="#0000ff", desc="cool")
        tag_repo.create(tag)
        found = tag_repo.find_by_name(_OWNER, "blue")
        assert found is not None
        assert found.description == "cool"

    def test_find_by_name_not_found(self, tag_repo):
        assert tag_repo.find_by_name(_OWNER, "nope") is None

    def test_find_by_owner(self, tag_repo):
        tag_repo.create(_make_tag(name="a", color="#aaaaaa", owner=_OWNER))
        tag_repo.create(_make_tag(name="b", color="#bbbbbb", owner=_OWNER))
        tag_repo.create(_make_tag(name="c", color="#cccccc", owner=_OWNER2))

        result = tag_repo.find_by_owner(_OWNER)
        assert len(result) == 2
        names = {t.name for t in result}
        assert names == {"a", "b"}

    def test_find_all(self, tag_repo):
        tag_repo.create(_make_tag(name="x", color="#111111", owner=_OWNER))
        tag_repo.create(_make_tag(name="y", color="#222222", owner=_OWNER2))
        assert len(tag_repo.find_all()) == 2

    def test_update_tag(self, tag_repo):
        tag = _make_tag(name="old", color="#000000", desc="before")
        tag_repo.create(tag)
        tag.name = "new"
        tag.color = "#ffffff"
        tag.description = "after"

        tag_repo.update_tag(tag.id, tag)

        found = tag_repo.find_by_id(tag.id)
        assert found.name == "new"
        assert found.color == "#ffffff"
        assert found.description == "after"

    def test_update_tag_not_found(self, tag_repo):
        ghost = DatasetTag(
            id=uuid.uuid4(), owner_id=_OWNER, name="ghost", color="#000000",
            description="", created_at=datetime.now(),
        )
        with pytest.raises(ValueError):
            tag_repo.update_tag(ghost.id, ghost)

    def test_delete_tag(self, tag_repo):
        tag = _make_tag(name="temp", color="#123456")
        tag_repo.create(tag)
        tag_repo.delete_tag(tag.id)
        assert tag_repo.find_by_id(tag.id) is None

    def test_delete_tag_not_found(self, tag_repo):
        with pytest.raises(ValueError):
            tag_repo.delete_tag(uuid.uuid4())

    def test_full_crud_flow(self, tag_repo):
        # create
        tag = _make_tag(name="e2e", color="#e2e2e2", desc="test")
        tag_repo.create(tag)
        found = tag_repo.find_by_name(_OWNER, "e2e")
        assert found is not None

        # update
        found.name = "e2e_updated"
        tag_repo.update_tag(found.id, found)
        assert tag_repo.find_by_id(found.id).name == "e2e_updated"

        # delete
        tag_repo.delete_tag(found.id)
        assert tag_repo.find_by_id(found.id) is None
