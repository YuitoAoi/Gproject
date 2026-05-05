import uuid
from datetime import datetime

import pytest

from src.core.user import User


def _make_user(name="alice", email="alice@test.com", password="secret") -> User:
    now = datetime.now()
    return User(
        id=uuid.uuid4(),
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

    def test_create_returns_none(self, repo):
        """create 现在返回 None（void），异常向上传播"""
        user = _make_user()
        result = repo.create(user)
        assert result is None

    def test_create_duplicate_name_allowed(self, repo):
        """重复 name 允许（name 上无唯一约束）"""
        repo.create(_make_user(name="bob", email="bob1@test.com"))
        repo.create(_make_user(name="bob", email="bob2@test.com"))
        # 不抛异常即通过

    def test_create_duplicate_email_raises(self, repo):
        """重复 email 应触发数据库唯一约束"""
        repo.create(_make_user(name="carol", email="carol@test.com"))
        with pytest.raises(Exception):
            repo.create(_make_user(name="carol2", email="carol@test.com"))

    # ── find_by_id ─────────────────────────────────────────────

    def test_find_by_id_found(self, repo):
        user = _make_user()
        repo.create(user)
        found = repo.find_by_id(user.id)

        assert found is not None
        assert found.id == user.id
        assert found.name == user.name
        assert found.email == user.email

    def test_find_by_id_not_found(self, repo):
        found = repo.find_by_id(uuid.uuid4())
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
        user = _make_user()
        repo.create(user)
        assert repo.exists(user.id) is True

    def test_exists_false(self, repo):
        assert repo.exists(uuid.uuid4()) is False

    # ── update ─────────────────────────────────────────────────

    def test_update_success(self, repo):
        user = _make_user(name="frank", email="frank@test.com")
        repo.create(user)

        updated_data = _make_user(name="frank_new", email="frank_new@test.com", password="newpass")
        updated_data.id = user.id
        repo.update(user.id, updated_data)

        refetched = repo.find_by_id(user.id)
        assert refetched.name == "frank_new"
        assert refetched.email == "frank_new@test.com"
        assert refetched.password == "newpass"

    def test_update_not_found(self, repo):
        with pytest.raises(ValueError):
            repo.update(uuid.uuid4(), _make_user())

    # ── remove ─────────────────────────────────────────────────

    def test_remove_success(self, repo):
        user = _make_user(name="grace")
        repo.create(user)
        repo.remove(user.id)

        # 确认已删除
        assert repo.find_by_id(user.id) is None

    def test_remove_not_found(self, repo):
        assert repo.remove(uuid.uuid4()) is None

    # ── 端到端流程 ────────────────────────────────────────────

    def test_full_crud_flow(self, repo):
        """创建 → 查找 → 更新 → 删除 完整链路"""
        # create
        user = _make_user(name="e2e", email="e2e@test.com", password="pwd")
        repo.create(user)

        # find_by_id
        found = repo.find_by_id(user.id)
        assert found.name == "e2e"

        # exists
        assert repo.exists(user.id) is True

        # update
        updated = _make_user(name="e2e_updated", email="e2e_new@test.com")
        updated.id = user.id
        repo.update(user.id, updated)

        found2 = repo.find_by_id(user.id)
        assert found2.name == "e2e_updated"

        # remove
        repo.remove(user.id)
        assert repo.find_by_id(user.id) is None
        assert repo.exists(user.id) is False
