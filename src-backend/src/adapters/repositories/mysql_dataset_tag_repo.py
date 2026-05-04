from typing import List, Optional, cast
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session

from src.core.dataset_tag import DatasetTag
from src.services.interfaces.dataset_tag_repository import DatasetTagRepository
from src.services.interfaces.db_conn import DatabaseConnection


class MysqlDatasetTagRepository(DatasetTagRepository):
    """基于 SQLAlchemy + MySQL 的数据集标签仓储实现。

    所有写方法返回 Optional[Exception]：成功返回 None，失败返回异常对象。
    """

    _COLUMNS = ("id, owner_id, name, color, description, created_at")

    def __init__(self, connection: DatabaseConnection) -> None:
        self._conn = connection

    def _session(self) -> Session:
        return cast(Session, self._conn.new_session())

    # ── 表初始化 ──────────────────────────────────────────────

    def init_table(self) -> None:
        """确保 dataset_tags 表结构与实体匹配。"""
        with self._session() as s:
            s.execute(text("""
                CREATE TABLE IF NOT EXISTS dataset_tags (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    owner_id INT NOT NULL DEFAULT 0,
                    name VARCHAR(255) NOT NULL,
                    color VARCHAR(50) NOT NULL DEFAULT '#808080',
                    description TEXT,
                    created_at DATETIME NOT NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """))
            s.commit()

    # ── DatasetTagRepository 实现 ─────────────────────────────

    def create(self, name: str, color: str, desc: str, owner: int) -> Optional[Exception]:
        try:
            existing = self.find_by_name(owner, name)
            if existing is not None:
                return ValueError(f"Tag name already exists for this user: {name}")
            with self._session() as session:
                session.execute(
                    text(
                        "INSERT INTO dataset_tags "
                        "(owner_id, name, color, description, created_at) "
                        "VALUES (:owner_id, :name, :color, :description, :created_at)"
                    ),
                    {
                        "owner_id": owner,
                        "name": name,
                        "color": color,
                        "description": desc,
                        "created_at": datetime.now(),
                    },
                )
                session.commit()
                return None
        except Exception as exc:
            return exc

    def find_by_id(self, tag_id: int) -> Optional[DatasetTag]:
        try:
            with self._session() as session:
                row = session.execute(
                    text(f"SELECT {self._COLUMNS} FROM dataset_tags WHERE id = :id"),
                    {"id": tag_id},
                ).fetchone()
                if row is None:
                    return None
                return self._row_to_tag(row)
        except Exception:
            return None

    def find_by_name(self, owner_id: int, name: str) -> Optional[DatasetTag]:
        try:
            with self._session() as session:
                row = session.execute(
                    text(
                        f"SELECT {self._COLUMNS} FROM dataset_tags "
                        "WHERE owner_id = :owner_id AND name = :name"
                    ),
                    {"owner_id": owner_id, "name": name},
                ).fetchone()
                if row is None:
                    return None
                return self._row_to_tag(row)
        except Exception:
            return None

    def find_by_owner(self, owner_id: int) -> List[DatasetTag]:
        try:
            with self._session() as session:
                rows = session.execute(
                    text(
                        f"SELECT {self._COLUMNS} FROM dataset_tags "
                        "WHERE owner_id = :owner_id ORDER BY id DESC"
                    ),
                    {"owner_id": owner_id},
                ).fetchall()
                return [self._row_to_tag(r) for r in rows]
        except Exception:
            return []

    def find_all(self) -> List[DatasetTag]:
        try:
            with self._session() as session:
                rows = session.execute(
                    text(f"SELECT {self._COLUMNS} FROM dataset_tags ORDER BY id DESC"),
                ).fetchall()
                return [self._row_to_tag(r) for r in rows]
        except Exception:
            return []

    def update_tag(self, tag_id: int, tag: DatasetTag) -> Optional[Exception]:
        try:
            with self._session() as session:
                result = cast(CursorResult, session.execute(
                    text(
                        "UPDATE dataset_tags SET "
                        "owner_id = :owner_id, name = :name, color = :color, "
                        "description = :description "
                        "WHERE id = :id"
                    ),
                    {
                        "id": tag_id,
                        "owner_id": tag.owner_id,
                        "name": tag.name,
                        "color": tag.color,
                        "description": tag.description,
                    },
                ))
                session.commit()
                if result.rowcount == 0:
                    return ValueError(f"Tag not found: {tag_id}")
                return None
        except Exception as exc:
            return exc

    def delete_tag(self, tag_id: int) -> Optional[Exception]:
        try:
            with self._session() as session:
                result = cast(CursorResult, session.execute(
                    text("DELETE FROM dataset_tags WHERE id = :id"),
                    {"id": tag_id},
                ))
                session.commit()
                if result.rowcount == 0:
                    return ValueError(f"Tag not found: {tag_id}")
                return None
        except Exception as exc:
            return exc

    # ── 内部工具 ───────────────────────────────────────────────

    @staticmethod
    def _row_to_tag(row) -> DatasetTag:
        return DatasetTag(
            id=row.id,
            owner_id=row.owner_id,
            name=row.name,
            color=row.color,
            description=row.description or "",
            created_at=_ensure_datetime(row.created_at),
        )


def _ensure_datetime(value) -> datetime:
    if isinstance(value, datetime):
        return value
    if value is not None:
        return datetime.fromisoformat(str(value))
    return value
