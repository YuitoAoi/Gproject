import sys
from pathlib import Path

import pytest

# 解决 user_login_service.py 中 `from interfaces.user_repository import ...`
# 等相对导入问题
_SERVICES_DIR = Path(__file__).resolve().parent.parent / "src" / "services"
if str(_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(_SERVICES_DIR))

from sqlalchemy import text

from src.core.config import config
from src.db_connections.mysql import MysqlDatabaseConnection
from src.adapters.repositories.mysql_user_repo import MysqlUserRepository

TEST_DB_URL = config.DATABASE_URL

CREATE_USERS_TABLE = text(
    "CREATE TABLE IF NOT EXISTS users ("
    "  id INT AUTO_INCREMENT PRIMARY KEY,"
    "  name VARCHAR(255) NOT NULL UNIQUE,"
    "  email VARCHAR(255) NOT NULL UNIQUE,"
    "  password VARCHAR(255) NOT NULL,"
    "  is_admin BOOLEAN DEFAULT FALSE,"
    "  is_active BOOLEAN DEFAULT TRUE,"
    "  created_at DATETIME NOT NULL,"
    "  last_login DATETIME NOT NULL"
    ")"
)

TRUNCATE_USERS = text("DELETE FROM users")


@pytest.fixture(scope="session")
def db_connection():
    """会话级：创建数据库连接，建表，测试结束后释放。"""
    conn = MysqlDatabaseConnection(TEST_DB_URL, echo=False)
    conn.start()

    # 确保 users 表存在
    with conn.new_session() as session:
        session.execute(CREATE_USERS_TABLE)
        session.commit()

    yield conn

    conn.dispose()


@pytest.fixture
def repo(db_connection):
    """函数级：每个测试前清空 users 表，提供干净的仓储实例。"""
    with db_connection.new_session() as session:
        session.execute(TRUNCATE_USERS)
        session.commit()

    return MysqlUserRepository(db_connection)
