"""标签仓储实现 —— 通过 SQLAlchemy 自动适配 MySQL / SQLite。"""
import logging
from datetime import datetime
from typing import List, Optional, cast

from sqlalchemy import Column, DateTime, Integer, MetaData, String, Table, Text, text
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session

from src.adapters.repositories._utils import ensure_datetime
from src.core.dataset_tag import DatasetTag
from src.services.interfaces.dataset_tag_repository import DatasetTagRepository
from src.services.interfaces.db_conn import DatabaseConnection

_logger = logging.getLogger(__name__)

_metadata = MetaData()

_tag_table = Table(
    "dataset_tags",
    _metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("owner_id", Integer, nullable=False, default=0),
    Column("name", String(255), nullable=False),
    Column("color", String(50), nullable=False, default="#808080"),
    Column("description", Text),
    Column("created_at", DateTime, nullable=False),
)


class DatasetTagRepositoryAdapter(DatasetTagRepository):
    """标签仓储实现。SQLAlchemy Core Table 自动适配 MySQL / SQLite。"""

    _COLUMNS = ("id, owner_id, name, color, description, created_at")

    def __init__(self, connection: DatabaseConnection) -> None:
        self._conn = connection

    def _session(self) -> Session:
        return cast(Session, self._conn.new_session())

    # ── 表初始化 ──────────────────────────────────────────────

    def init_table(self) -> None:
        self._conn.start()
        assert self._conn.engine is not None
        _metadata.create_all(self._conn.engine)

    def ensure_indexes(self) -> None:
        """确保标签表存在唯一约束（owner_id + name）。"""
        with self._session() as s:
            try:
                s.execute(text(
                    "CREATE UNIQUE INDEX uq_dataset_tags_owner_name "
                    "ON dataset_tags (owner_id, name)"
                ))
                s.commit()
            except Exception as e:
                s.rollback()
                if "Duplicate key name" in str(e) or "1061" in str(e):
                    return
                _logger.exception("Failed to ensure tag unique index")

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
            _logger.exception("Failed to find tag by id=%s", tag_id)
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
            _logger.exception("Failed to find tag by owner_id=%s name=%s", owner_id, name)
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
            _logger.exception("Failed to find tags by owner_id=%s", owner_id)
            return []

    def find_all(self) -> List[DatasetTag]:
        try:
            with self._session() as session:
                rows = session.execute(
                    text(f"SELECT {self._COLUMNS} FROM dataset_tags ORDER BY id DESC"),
                ).fetchall()
                return [self._row_to_tag(r) for r in rows]
        except Exception:
            _logger.exception("Failed to find all tags")
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
            created_at=ensure_datetime(row.created_at),
        )
