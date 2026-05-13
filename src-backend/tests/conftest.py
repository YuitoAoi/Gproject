# ruff: noqa: RUF002
from __future__ import annotations

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from src.adapters.repositories.user_repo import UserRepositoryAdapter

TRUNCATE_USERS = text("DELETE FROM users")


class _SqliteTestConnection:
    """轻量级 SQLite 测试连接辅助类，仅用于 pytest。"""

    def __init__(self, database_url: str = "sqlite:///:memory:", *, echo: bool = False) -> None:
        self._engine = create_engine(database_url, echo=echo, future=True)
        self._session_factory = sessionmaker(bind=self._engine, expire_on_commit=False, class_=Session)

    def new_session(self) -> Session:
        return self._session_factory()

    def dispose(self) -> None:
        self._engine.dispose()


@pytest.fixture(scope="session")
def db_connection() -> Generator[_SqliteTestConnection, None, None]:
    """会话级：SQLite :memory: 连接，测试结束后释放。"""
    conn = _SqliteTestConnection("sqlite:///:memory:", echo=False)
    UserRepositoryAdapter(conn).init_table()
    yield conn
    conn.dispose()


@pytest.fixture
def repo(db_connection: _SqliteTestConnection) -> UserRepositoryAdapter:
    """函数级：每个测试前清空 users 表。"""
    with db_connection.new_session() as session:
        session.execute(TRUNCATE_USERS)
        session.commit()
    return UserRepositoryAdapter(db_connection)
