import sys
from pathlib import Path

import pytest

_SERVICES_DIR = Path(__file__).resolve().parent.parent / "src" / "services"
if str(_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(_SERVICES_DIR))

from sqlalchemy import text

from src.db_connections.sqlite import SqliteConnection
from src.adapters.repositories.user_repo import UserRepositoryAdapter

TRUNCATE_USERS = text("DELETE FROM users")


@pytest.fixture(scope="session")
def db_connection():
    """会话级：SQLite :memory: 连接，测试结束后释放。"""
    conn = SqliteConnection("sqlite:///:memory:", echo=False)
    conn.start()

    UserRepositoryAdapter(conn).init_table()

    yield conn
    conn.dispose()


@pytest.fixture
def repo(db_connection):
    """函数级：每个测试前清空 users 表。"""
    with db_connection.new_session() as session:
        session.execute(TRUNCATE_USERS)
        session.commit()
    return UserRepositoryAdapter(db_connection)
