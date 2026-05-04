from __future__ import annotations

from typing import Any

from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from src.services.interfaces.db_conn import DatabaseConnection


class SqliteConnection(DatabaseConnection):
    """基于 SQLAlchemy 的 SQLite 数据库连接实现。

    默认启用 WAL 模式和外键约束。

    使用示例::

        conn = SqliteConnection("sqlite:///gproject.db")
        conn.start()
        session = conn.new_session()
        session.close()
        conn.dispose()
    """

    def __init__(
        self,
        database_url: str,
        *,
        echo: bool = False,
        **engine_kwargs: Any,
    ) -> None:
        self._database_url = database_url
        self._echo = echo
        self._engine_kwargs = engine_kwargs
        self._engine: Engine | None = None
        self._session_factory: sessionmaker[Session] | None = None
        self._started = False

    # ── DatabaseConnection 实现 ────────────────────────────────

    def start(self, **kwargs: Any) -> None:
        if self._started:
            return

        self._engine = create_engine(
            self._database_url,
            connect_args={"check_same_thread": False},
            echo=self._echo,
            **self._engine_kwargs,
        )

        event.listen(self._engine, "connect", self._on_connect)

        with self._engine.connect() as conn:
            conn.execute(text("SELECT 1"))

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

    # ── 属性 ──────────────────────────────────────────────────

    @property
    def engine(self) -> Engine:
        self._ensure_started()
        assert self._engine is not None
        return self._engine

    @property
    def is_connected(self) -> bool:
        if not self._started or self._engine is None:
            return False
        try:
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    # ── 内部 ──────────────────────────────────────────────────

    @staticmethod
    def _on_connect(dbapi_connection: Any, connection_record: Any) -> None:
        dbapi_connection.execute("PRAGMA journal_mode=WAL")
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    def _ensure_started(self) -> None:
        if not self._started:
            raise RuntimeError("SqliteConnection 尚未启动，请先调用 .start()")

    def __repr__(self) -> str:
        return f"<SqliteConnection url={self._database_url} started={self._started}>"


def create_sqlite_connection(path: str) -> SqliteConnection:
    """便捷工厂：从文件路径创建 SQLite 连接。"""
    return SqliteConnection(f"sqlite:///{path}")
