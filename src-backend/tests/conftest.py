import sys
from pathlib import Path

import pytest

_SERVICES_DIR = Path(__file__).resolve().parent.parent / "src" / "services"
if str(_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(_SERVICES_DIR))

from sqlalchemy import text

from src.db_connections.mysql import MysqlConnection
from src.adapters.repositories.user_repo import UserRepositoryAdapter
from tests import get_test_db_url

TRUNCATE_USERS = text("DELETE FROM users")
TRUNCATE_USERS_MYSQL = text("TRUNCATE TABLE users")


def _get_test_db_url() -> str:
    return get_test_db_url()


@pytest.fixture(scope="session")
def db_connection():
    """会话级：MySQL 测试数据库连接，测试结束后释放。"""
    conn = MysqlConnection(_get_test_db_url(), echo=False, pool_size=5, max_overflow=5)
    conn.start()

    UserRepositoryAdapter(conn).init_table()

    yield conn
    conn.dispose()


@pytest.fixture
def repo(db_connection):
    """函数级：每个测试前清空 users 表。"""
    with db_connection.new_session() as session:
        try:
            session.execute(TRUNCATE_USERS_MYSQL)
        except Exception:
            session.execute(TRUNCATE_USERS)
        session.commit()
    return UserRepositoryAdapter(db_connection)
