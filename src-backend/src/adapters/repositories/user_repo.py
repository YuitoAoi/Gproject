"""用户仓储实现 —— 通过 SQLAlchemy 自动适配 MySQL / SQLite。"""
from datetime import datetime
from typing import List, Optional, cast

from sqlalchemy import Boolean, Column, DateTime, Integer, MetaData, String, Table, text
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session

from src.adapters.repositories._utils import ensure_datetime
from src.core.user import User
from src.services.interfaces.db_conn import DatabaseConnection
from src.services.interfaces.user_repository import UserRepository

_metadata = MetaData()

_user_table = Table(
    "users",
    _metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(255), nullable=False),
    Column("email", String(255), nullable=False, unique=True),
    Column("password", String(255), nullable=False),
    Column("is_admin", Boolean, default=False),
    Column("is_active", Boolean, default=True),
    Column("created_at", DateTime, nullable=False),
    Column("last_login", DateTime, nullable=False),
    Column("last_login_ip", String(45), default=""),
)


class UserRepositoryAdapter(UserRepository):
    """用户仓储实现。SQLAlchemy Core Table 自动适配 MySQL / SQLite。"""

    _COLUMNS = ("id, name, email, password, is_admin, is_active, "
                "created_at, last_login, last_login_ip")

    def __init__(self, connection: DatabaseConnection) -> None:
        self._conn = connection

    def _session(self) -> Session:
        return cast(Session, self._conn.new_session())

    # ── 表初始化 ──────────────────────────────────────────────

    def init_table(self) -> None:
        self._conn.start()
        assert self._conn.engine is not None
        _metadata.create_all(self._conn.engine)

        # 补齐旧表缺失的列
        with self._session() as s:
            for col, col_def in [
                ("last_login_ip", "VARCHAR(45) DEFAULT ''"),
            ]:
                try:
                    s.execute(text(f"ALTER TABLE users ADD COLUMN {col} {col_def}"))
                    s.commit()
                except Exception:
                    s.rollback()

    # ── UserRepository 实现 ────────────────────────────────────

    def create(self, user: User) -> Optional[int]:
        with self._session() as session:
            result = session.execute(
                text(
                    "INSERT INTO users "
                    "(name, email, password, is_admin, is_active, created_at, last_login) "
                    "VALUES (:name, :email, :password, :is_admin, :is_active, :created_at, :last_login)"
                ),
                {
                    "name": user.name,
                    "email": user.email,
                    "password": user.password,
                    "is_admin": user.is_admin,
                    "is_active": user.is_active,
                    "created_at": user.created_at,
                    "last_login": user.last_login,
                    "last_login_ip": user.last_login_ip,
                },
            )
            session.commit()
            return cast(CursorResult, result).lastrowid

    def find_by_id(self, id: int) -> Optional[User]:
        with self._session() as session:
            row = session.execute(
                text(f"SELECT {self._COLUMNS} FROM users WHERE id = :id"),
                {"id": id},
            ).fetchone()
            if row is None:
                return None
            return self._row_to_user(row)

    def find_by_name(self, name: str) -> Optional[User]:
        with self._session() as session:
            row = session.execute(
                text(f"SELECT {self._COLUMNS} FROM users WHERE name = :name"),
                {"name": name},
            ).fetchone()
            if row is None:
                return None
            return self._row_to_user(row)

    def find_by_email(self, email: str) -> Optional[User]:
        with self._session() as session:
            row = session.execute(
                text(f"SELECT {self._COLUMNS} FROM users WHERE email = :email"),
                {"email": email},
            ).fetchone()
            if row is None:
                return None
            return self._row_to_user(row)

    def find_all(self) -> List[User]:
        with self._session() as session:
            rows = session.execute(
                text(f"SELECT {self._COLUMNS} FROM users"),
            ).fetchall()
            return [self._row_to_user(r) for r in rows]

    def exists(self, id: int) -> bool:
        with self._session() as session:
            result = session.execute(
                text("SELECT 1 FROM users WHERE id = :id"),
                {"id": id},
            ).fetchone()
            return result is not None

    def update(self, id: int, user: User) -> Optional[User]:
        with self._session() as session:
            result = cast(CursorResult, session.execute(
                text(
                    "UPDATE users SET "
                    "name = :name, email = :email, password = :password, "
                    "is_admin = :is_admin, is_active = :is_active, "
                    "created_at = :created_at, last_login = :last_login "
                    "WHERE id = :id"
                ),
                {
                    "id": id,
                    "name": user.name,
                    "email": user.email,
                    "password": user.password,
                    "is_admin": user.is_admin,
                    "is_active": user.is_active,
                    "created_at": user.created_at,
                    "last_login": user.last_login,
                    "last_login_ip": user.last_login_ip,
                },
            ))
            session.commit()
            if result.rowcount == 0:
                return None
            return self.find_by_id(id)

    def remove(self, id: int) -> Optional[User]:
        user = self.find_by_id(id)
        if user is None:
            return None
        with self._session() as session:
            session.execute(
                text("DELETE FROM users WHERE id = :id"),
                {"id": id},
            )
            session.commit()
        return user

    # ── 内部工具 ───────────────────────────────────────────────

    @staticmethod
    def _row_to_user(row) -> User:
        return User(
            id=row.id,
            name=row.name,
            email=row.email,
            password=row.password,
            is_admin=bool(row.is_admin),
            is_active=bool(row.is_active),
            created_at=ensure_datetime(row.created_at),
            last_login=ensure_datetime(row.last_login),
            last_login_ip=row.last_login_ip or "",
        )
