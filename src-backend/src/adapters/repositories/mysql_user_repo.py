from typing import List, Optional, cast
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session

from src.services.interfaces.user_repository import UserRepository
from src.services.interfaces.db_conn import DatabaseConnection
from src.core.user import User


class MysqlUserRepository(UserRepository):
    """基于 SQLAlchemy + MySQL 的用户仓储实现。

    使用示例::

        conn = MysqlDatabaseConnection(url)
        conn.start()
        repo = MysqlUserRepository(conn)
        repo.create(user)
    """

    _COLUMNS = ("id, name, email, password, is_admin, is_active, "
                "created_at, last_login")

    def __init__(self, connection: DatabaseConnection) -> None:
        self._conn = connection

    def _session(self) -> Session:
        return cast(Session, self._conn.new_session())

    # ── UserRepository 实现 ────────────────────────────────────

    def create(self, user: User) -> Optional[int]:
        with self._session() as session:
            session.execute(
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
                },
            )
            session.commit()
            pk = session.execute(text("SELECT LAST_INSERT_ID()")).scalar()
            return pk

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
            created_at=_ensure_datetime(row.created_at),
            last_login=_ensure_datetime(row.last_login),
        )


def _ensure_datetime(value) -> datetime:
    if isinstance(value, datetime):
        return value
    if value is not None:
        return datetime.fromisoformat(str(value))
    return value
