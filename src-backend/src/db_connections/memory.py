from __future__ import annotations

from typing import Any

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from src.services.interfaces.db_conn import DatabaseConnection


class MemoryDatabaseConnection(DatabaseConnection):
    """基于 SQLAlchemy + SQLite :memory: 的内存数据库连接。

    适用于测试场景，进程结束即销毁。
    """

    def __init__(self, *, echo: bool = False) -> None:
        self._echo = echo
        self._engine: Engine | None = None
        self._session_factory: sessionmaker[Session] | None = None
        self._started = False

    def start(self, **kwargs: Any) -> None:
        if self._started:
            return
        self._engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            echo=self._echo,
        )
        event.listen(self._engine, "connect", self._on_connect)
        self._session_factory = sessionmaker(
            bind=self._engine, autoflush=False, autocommit=False
        )
        self._started = True

    def new_session(self) -> Session:
        self._ensure_started()
        assert self._session_factory is not None
        return self._session_factory()

    def dispose(self) -> None:
        if self._engine is not None:
            self._engine.dispose()
        self._engine = None
        self._session_factory = None
        self._started = False

    def create_tables(self, base: Any) -> None:
        self._ensure_started()
        base.metadata.create_all(self._engine)

    def drop_tables(self, base: Any) -> None:
        self._ensure_started()
        base.metadata.drop_all(self._engine)

    @staticmethod
    def _on_connect(dbapi_connection: Any, connection_record: Any) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()

    def _ensure_started(self) -> None:
        if not self._started:
            raise RuntimeError(
                "MemoryDatabaseConnection 尚未启动，请先调用 .start()"
            )

    def __repr__(self) -> str:
        return f"<MemoryDatabaseConnection started={self._started}>"
