from __future__ import annotations

from typing import Any

from sqlalchemy import Engine, create_engine, event, pool, text
from sqlalchemy.orm import Session, sessionmaker

from src.services.interfaces.db_conn import DatabaseConnection


class MysqlConnection(DatabaseConnection):
    """基于 SQLAlchemy 的 MySQL 数据库连接实现。

    使用 pymysql 驱动，连接池大小为 20，自动检测断连并重连。
    通过 start() 延迟初始化引擎，支持 create_tables / drop_tables。

    使用示例::

        conn = MysqlDatabaseConnection("mysql+pymysql://user:pass@host/db")
        conn.start()
        session = conn.new_session()
        try:
            result = session.execute(...)
        finally:
            session.close()
        conn.dispose()
    """

    # ══════════════════════════════════════════════════════════
    # 初始化
    # ══════════════════════════════════════════════════════════

    def __init__(
        self,
        database_url: str,
        *,
        pool_size: int = 10,
        max_overflow: int = 10,
        pool_recycle: int = 3600,
        echo: bool = False,
        **engine_kwargs: Any,
    ) -> None:
        self._database_url = database_url
        self._pool_size = pool_size
        self._max_overflow = max_overflow
        self._pool_recycle = pool_recycle
        self._echo = echo
        self._engine_kwargs = engine_kwargs
        self._engine: Engine | None = None
        self._session_factory: sessionmaker[Session] | None = None
        self._started = False

    # ══════════════════════════════════════════════════════════
    # DatabaseConnection 实现
    # ══════════════════════════════════════════════════════════

    def start(self, **kwargs: Any) -> None:
        if self._started:
            return
        retries = kwargs.pop("_retries", 3)
        import time, logging
        logger = logging.getLogger(__name__)
        last_error = None

        for attempt in range(1, retries + 1):
            try:
                self._engine = create_engine(
                    self._database_url,
                    poolclass=pool.QueuePool,
                    pool_size=self._pool_size,
                    max_overflow=self._max_overflow,
                    pool_recycle=self._pool_recycle,
                    pool_pre_ping=True,
                    echo=self._echo,
                    **self._engine_kwargs,
                )
                with self._engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                event.listen(self._engine, "connect", self._on_connect)
                self._session_factory = sessionmaker(bind=self._engine, autoflush=False, autocommit=False)
                self._started = True
                return
            except Exception as e:
                last_error = e
                if self._engine:
                    self._engine.dispose()
                    self._engine = None
                if attempt < retries:
                    wait = 2 ** attempt
                    logger.warning(
                        f"MySQL connection attempt {attempt}/{retries} failed, "
                        f"retrying in {wait}s: {e}"
                    )
                    # 可中断 sleep：每 0.1s 检查一次，支持 Ctrl+C
                    for _ in range(int(wait * 10)):
                        time.sleep(0.1)

        logger.error(f"MySQL connection failed after {retries} attempts: {last_error}")
        raise RuntimeError(f"MySQL unavailable after {retries} retries") from last_error

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

    # ══════════════════════════════════════════════════════════
    # 内部
    # ══════════════════════════════════════════════════════════

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

    @staticmethod
    def _on_connect(dbapi_connection: Any, connection_record: Any) -> None:  # pragma: no cover
        """连接建立后回调：设置 utf8mb4。"""
        cursor = dbapi_connection.cursor()
        cursor.execute("SET NAMES utf8mb4")
        cursor.close()

    def _ensure_started(self) -> None:
        if not self._started:
            raise RuntimeError(
                "MysqlDatabaseConnection 尚未启动，请先调用 .start()"
            )

    def __repr__(self) -> str:
        return f"<MysqlDatabaseConnection url={_mask_url(self._database_url)} started={self._started}>"


def _mask_url(url: str) -> str:
    if "@" in url:
        prefix, rest = url.split("@", 1)
        if "://" in prefix:
            scheme, creds = prefix.split("://", 1)
            if ":" in creds:
                user, _ = creds.split(":", 1)
                return f"{scheme}://{user}:***@{rest}"
    return url
