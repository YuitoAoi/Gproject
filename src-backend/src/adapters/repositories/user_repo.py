# ruff: noqa: RUF002
"""用户仓储实现 —— 通过 SQLAlchemy 自动适配 MySQL / SQLite。"""

from typing import cast

from sqlalchemy import Boolean, Column, DateTime, Integer, MetaData, String, Table, text
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session
from src.adapters.repositories._utils import ensure_datetime
from src.core.user import User
from src.services.interfaces.db_conn import DatabaseConnection
from src.services.interfaces.user_repository import PaginatedUsers, UserRepository

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
    Column("avatar", String(500), default="/static/avatars/default.jpg"),
)


class UserRepositoryAdapter(UserRepository):
    """用户仓储实现。SQLAlchemy Core Table 自动适配 MySQL / SQLite。

    异常策略：CRUD 操作不捕获异常，直接向上传播给 Service 层处理。
    """

    _COLUMNS = "id, name, email, password, is_admin, is_active, created_at, last_login, last_login_ip, avatar"

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
                ("avatar", "VARCHAR(500) DEFAULT '/static/avatars/default.jpg'"),
            ]:
                try:
                    s.execute(text(f"ALTER TABLE users ADD COLUMN {col} {col_def}"))
                    s.commit()
                except Exception:
                    s.rollback()

    # ── UserRepository 实现 ────────────────────────────────────

    def create(self, user: User) -> int | None:
        with self._session() as session:
            result = session.execute(
                text(
                    "INSERT INTO users "
                    "(name, email, password, is_admin, is_active, created_at, last_login, last_login_ip, avatar) "
                    "VALUES (:name, :email, :password, :is_admin, :is_active, :created_at, :last_login, :last_login_ip, :avatar)"
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
                    "avatar": user.avatar,
                },
            )
            session.commit()
            return cast(CursorResult, result).lastrowid

    def find_by_id(self, id: int) -> User | None:
        with self._session() as session:
            row = session.execute(
                text(f"SELECT {self._COLUMNS} FROM users WHERE id = :id"),
                {"id": id},
            ).fetchone()
            if row is None:
                return None
            return self._row_to_user(row)

    def find_by_name(self, name: str) -> User | None:
        with self._session() as session:
            row = session.execute(
                text(f"SELECT {self._COLUMNS} FROM users WHERE name = :name"),
                {"name": name},
            ).fetchone()
            if row is None:
                return None
            return self._row_to_user(row)

    def find_by_email(self, email: str) -> User | None:
        with self._session() as session:
            row = session.execute(
                text(f"SELECT {self._COLUMNS} FROM users WHERE email = :email"),
                {"email": email},
            ).fetchone()
            if row is None:
                return None
            return self._row_to_user(row)

    def find_all(self) -> list[User]:
        with self._session() as session:
            rows = session.execute(
                text(f"SELECT {self._COLUMNS} FROM users"),
            ).fetchall()
            return [self._row_to_user(r) for r in rows]

    def find_all_paginated(
        self, page: int, size: int, keyword: str | None = None
    ) -> PaginatedUsers:
        with self._session() as session:
            where = ""
            params: dict = {}
            if keyword:
                where = "WHERE name LIKE :kw OR email LIKE :kw"
                params["kw"] = f"%{keyword}%"

            count_row = session.execute(
                text(f"SELECT COUNT(*) as cnt FROM users {where}"),
                params,
            ).fetchone()
            total = count_row.cnt if count_row else 0

            params["limit"] = size
            params["offset"] = (page - 1) * size
            rows = session.execute(
                text(
                    f"SELECT {self._COLUMNS} FROM users {where} "
                    "ORDER BY id ASC LIMIT :limit OFFSET :offset"
                ),
                params,
            ).fetchall()
            return PaginatedUsers(
                records=[self._row_to_user(r) for r in rows],
                total=total,
                current=page,
                size=size,
            )

    def exists(self, id: int) -> bool:
        with self._session() as session:
            result = session.execute(
                text("SELECT 1 FROM users WHERE id = :id"),
                {"id": id},
            ).fetchone()
            return result is not None

    def update(self, id: int, user: User) -> User | None:
        with self._session() as session:
            result = cast(
                CursorResult,
                session.execute(
                    text(
                        "UPDATE users SET "
                        "name = :name, email = :email, password = :password, "
                        "is_admin = :is_admin, is_active = :is_active, "
                        "created_at = :created_at, last_login = :last_login, "
                        "last_login_ip = :last_login_ip, avatar = :avatar "
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
                        "avatar": user.avatar,
                    },
                ),
            )
            session.commit()
            if result.rowcount == 0:
                return None
            return self.find_by_id(id)

    def remove(self, id: int) -> User | None:
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
            avatar=row.avatar or "/static/avatars/default.jpg",
        )
