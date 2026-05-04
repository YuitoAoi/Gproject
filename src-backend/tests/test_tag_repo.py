"""DatasetTagRepositoryAdapter 集成测试"""
from datetime import datetime

import pytest

from src.db_connections.sqlite import SqliteConnection
from src.adapters.repositories.dataset_tag_repo import DatasetTagRepositoryAdapter


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
        err = tag_repo.create(name="red", color="#ff0000", desc="warm", owner=1)
        assert err is None

    def test_create_duplicate_name_same_owner(self, tag_repo):
        tag_repo.create(name="dup", color="#111", desc="", owner=1)
        err = tag_repo.create(name="dup", color="#222", desc="", owner=1)
        assert isinstance(err, ValueError)
        assert "already exists" in str(err)

    def test_create_same_name_diff_owner(self, tag_repo):
        err1 = tag_repo.create(name="shared", color="#333", desc="", owner=1)
        err2 = tag_repo.create(name="shared", color="#444", desc="", owner=2)
        assert err1 is None
        assert err2 is None

    def test_find_by_id(self, tag_repo):
        tag_repo.create(name="green", color="#0f0", desc="", owner=1)
        tag = tag_repo.find_by_name(1, "green")
        found = tag_repo.find_by_id(tag.id)
        assert found is not None
        assert found.name == "green"
        assert found.color == "#0f0"

    def test_find_by_id_not_found(self, tag_repo):
        assert tag_repo.find_by_id(999) is None

    def test_find_by_name(self, tag_repo):
        tag_repo.create(name="blue", color="#00f", desc="cool", owner=1)
        found = tag_repo.find_by_name(1, "blue")
        assert found is not None
        assert found.description == "cool"

    def test_find_by_name_not_found(self, tag_repo):
        assert tag_repo.find_by_name(1, "nope") is None

    def test_find_by_owner(self, tag_repo):
        tag_repo.create(name="a", color="#aaa", desc="", owner=1)
        tag_repo.create(name="b", color="#bbb", desc="", owner=1)
        tag_repo.create(name="c", color="#ccc", desc="", owner=2)

        result = tag_repo.find_by_owner(1)
        assert len(result) == 2
        names = {t.name for t in result}
        assert names == {"a", "b"}

    def test_find_all(self, tag_repo):
        tag_repo.create(name="x", color="#111", desc="", owner=1)
        tag_repo.create(name="y", color="#222", desc="", owner=2)
        assert len(tag_repo.find_all()) == 2

    def test_update_tag(self, tag_repo):
        tag_repo.create(name="old", color="#000", desc="before", owner=1)
        tag = tag_repo.find_by_name(1, "old")
        tag.name = "new"
        tag.color = "#fff"
        tag.description = "after"

        err = tag_repo.update_tag(tag.id, tag)
        assert err is None

        found = tag_repo.find_by_id(tag.id)
        assert found.name == "new"
        assert found.color == "#fff"
        assert found.description == "after"

    def test_update_tag_not_found(self, tag_repo):
        from src.core.dataset_tag import DatasetTag
        ghost = DatasetTag(
            id=999, owner_id=1, name="ghost", color="#000",
            description="", created_at=datetime.now(),
        )
        err = tag_repo.update_tag(999, ghost)
        assert isinstance(err, ValueError)

    def test_delete_tag(self, tag_repo):
        tag_repo.create(name="temp", color="#123", desc="", owner=1)
        tag = tag_repo.find_by_name(1, "temp")
        err = tag_repo.delete_tag(tag.id)
        assert err is None
        assert tag_repo.find_by_id(tag.id) is None

    def test_delete_tag_not_found(self, tag_repo):
        err = tag_repo.delete_tag(999)
        assert isinstance(err, ValueError)

    def test_full_crud_flow(self, tag_repo):
        # create
        err = tag_repo.create(name="e2e", color="#e2e", desc="test", owner=1)
        assert err is None
        tag = tag_repo.find_by_name(1, "e2e")
        assert tag is not None

        # update
        tag.name = "e2e_updated"
        err = tag_repo.update_tag(tag.id, tag)
        assert err is None
        assert tag_repo.find_by_id(tag.id).name == "e2e_updated"

        # delete
        err = tag_repo.delete_tag(tag.id)
        assert err is None
        assert tag_repo.find_by_id(tag.id) is None
