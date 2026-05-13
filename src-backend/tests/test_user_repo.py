# ruff: noqa: RUF002, RUF003, B017
from datetime import datetime

import pytest
from src.core.user import User


def _make_user(name="alice", email="alice@test.com", password="secret") -> User:
    now = datetime.now()
    return User(
        id=0,  # auto-increment，创建时占位
        name=name,
        email=email,
        password=password,
        is_admin=False,
        is_active=True,
        created_at=now,
        last_login=now,
    )


class TestUserRepositoryAdapter:
    """UserRepositoryAdapter 集成测试（SQLite :memory:）"""

    # ── create ─────────────────────────────────────────────────

    def test_create_returns_id(self, repo):
        """create 应返回自增主键"""
        user = _make_user()
        pk = repo.create(user)

        assert pk is not None
        assert pk > 0

    def test_create_duplicate_name_allowed(self, repo):
        """重复 name 允许（name 上无唯一约束）"""
        pk1 = repo.create(_make_user(name="bob", email="bob1@test.com"))
        pk2 = repo.create(_make_user(name="bob", email="bob2@test.com"))
        assert pk1 is not None
        assert pk2 is not None
        assert pk1 != pk2

    def test_create_duplicate_email_raises(self, repo):
        """重复 email 应触发数据库唯一约束"""
        repo.create(_make_user(name="carol", email="carol@test.com"))
        with pytest.raises(Exception):
            repo.create(_make_user(name="carol2", email="carol@test.com"))

    # ── find_by_id ─────────────────────────────────────────────

    def test_find_by_id_found(self, repo):
        user = _make_user()
        pk = repo.create(user)
        found = repo.find_by_id(pk)

        assert found is not None
        assert found.id == pk
        assert found.name == user.name
        assert found.email == user.email

    def test_find_by_id_not_found(self, repo):
        found = repo.find_by_id(99999)
        assert found is None

    # ── find_by_name ───────────────────────────────────────────

    def test_find_by_name_found(self, repo):
        user = _make_user(name="dave")
        repo.create(user)
        found = repo.find_by_name("dave")

        assert found is not None
        assert found.name == "dave"

    def test_find_by_name_not_found(self, repo):
        found = repo.find_by_name("nobody")
        assert found is None

    # ── find_by_email ──────────────────────────────────────────

    def test_find_by_email_found(self, repo):
        user = _make_user(email="eve@test.com")
        repo.create(user)
        found = repo.find_by_email("eve@test.com")

        assert found is not None
        assert found.email == "eve@test.com"

    def test_find_by_email_not_found(self, repo):
        found = repo.find_by_email("ghost@test.com")
        assert found is None

    # ── find_all ───────────────────────────────────────────────

    def test_find_all_empty(self, repo):
        result = repo.find_all()
        assert result == []

    def test_find_all_with_data(self, repo):
        repo.create(_make_user(name="u1", email="u1@test.com"))
        repo.create(_make_user(name="u2", email="u2@test.com"))
        result = repo.find_all()

        assert len(result) == 2
        names = {r.name for r in result}
        assert names == {"u1", "u2"}

    # ── exists ─────────────────────────────────────────────────

    def test_exists_true(self, repo):
        pk = repo.create(_make_user())
        assert repo.exists(pk) is True

    def test_exists_false(self, repo):
        assert repo.exists(99999) is False

    # ── update ─────────────────────────────────────────────────

    def test_update_success(self, repo):
        pk = repo.create(_make_user(name="frank", email="frank@test.com"))
        updated_data = _make_user(name="frank_new", email="frank_new@test.com", password="newpass")

        result = repo.update(pk, updated_data)

        assert result is not None
        assert result.id == pk
        assert result.name == "frank_new"
        assert result.email == "frank_new@test.com"
        assert result.password == "newpass"

        # 确认持久化
        refetched = repo.find_by_id(pk)
        assert refetched.name == "frank_new"

    def test_update_not_found(self, repo):
        result = repo.update(99999, _make_user())
        assert result is None

    # ── remove ─────────────────────────────────────────────────

    def test_remove_success(self, repo):
        pk = repo.create(_make_user(name="grace"))
        removed = repo.remove(pk)

        assert removed is not None
        assert removed.id == pk
        assert removed.name == "grace"

        # 确认已删除
        assert repo.find_by_id(pk) is None

    def test_remove_not_found(self, repo):
        assert repo.remove(99999) is None

    # ── 端到端流程 ────────────────────────────────────────────

    def test_full_crud_flow(self, repo):
        """创建 → 查找 → 更新 → 删除 完整链路"""
        # create
        user = _make_user(name="e2e", email="e2e@test.com", password="pwd")
        pk = repo.create(user)
        assert pk is not None

        # find_by_id
        found = repo.find_by_id(pk)
        assert found.name == "e2e"

        # exists
        assert repo.exists(pk) is True

        # update
        updated = _make_user(name="e2e_updated", email="e2e_new@test.com")
        result = repo.update(pk, updated)
        assert result.name == "e2e_updated"

        # remove
        removed = repo.remove(pk)
        assert removed.name == "e2e_updated"
        assert repo.exists(pk) is False
