"""
db_connections - SQLAlchemy 数据库连接基础设施

提供::

    Base            — ORM 模型基类 (declarative_base)
    session_scope   — 事务上下文管理器，自动 commit / rollback
    get_db          — FastAPI 依赖注入生成器
    MysqlDatabaseConnection  — MySQL 连接
    MemoryDatabaseConnection — SQLite :memory: 连接
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy.orm import DeclarativeBase, Session

from src.services.interfaces.db_conn import DatabaseConnection

from .memory import MemoryDatabaseConnection
from .mysql import MysqlDatabaseConnection

__all__ = [
    "Base",
    "get_db",
    "session_scope",
    "MysqlDatabaseConnection",
    "MemoryDatabaseConnection",
]

# ═══════════════════════════════════════════════
# ORM 模型基类
# ═══════════════════════════════════════════════


class Base(DeclarativeBase):
    """所有 SQLAlchemy ORM 模型的声明式基类。

    使用方式::

        from src.db_connections import Base
        from sqlalchemy import Column, Integer, String

        class User(Base):
            __tablename__ = "users"
            id = Column(Integer, primary_key=True)
            name = Column(String(50))
    """

    pass


# ═══════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════


@contextmanager
def session_scope(session_or_conn):
    """事务上下文管理器。

    退出时自动 commit；发生异常时自动 rollback。
    支持传入 DatabaseConnection（自动创建 session）或已存在的 Session。
    """

    if isinstance(session_or_conn, DatabaseConnection):
        session = session_or_conn.new_session()
        owned = True
    else:
        session = session_or_conn
        owned = False

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        if owned:
            session.close()


def get_db(connection: DatabaseConnection) -> Iterator[Session]:
    """FastAPI 依赖注入：每个请求获取独立 session，结束时自动关闭。

    使用方式::

        router = APIRouter()

        @router.get("/items")
        def list_items(db: Session = Depends(get_db)):
            ...
    """
    session = connection.new_session()
    try:
        yield session
    finally:
        session.close()
