"""
db_connections - SQLAlchemy 数据库连接基础设施
"""

from __future__ import annotations

from src.services.interfaces.db_conn import DatabaseConnection

from .mysql import MysqlConnection
from .sqlite import SqliteConnection

__all__ = [
    "MysqlConnection",
    "SqliteConnection",
    "create_db_connection",
]


def create_db_connection(database_url: str) -> DatabaseConnection:
    """根据 URL 协议自动选择数据库连接。

    ``sqlite:///`` → SqliteConnection
    ``mysql+pymysql://`` 或 ``mysql://`` → MysqlConnection
    """
    if database_url.startswith("sqlite"):
        return SqliteConnection(database_url)
    if database_url.startswith("mysql"):
        return MysqlConnection(database_url)
    raise ValueError(f"Unsupported database URL scheme: {database_url}")
