"""标签仓储实现 —— 通过 SQLAlchemy 自动适配 MySQL / SQLite。"""

import logging
from datetime import datetime
from typing import cast
import uuid

from sqlalchemy import Column, DateTime, MetaData, String, Table, Text, UniqueConstraint, text
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
    Column("id", String(36), primary_key=True),
    Column("owner_id", String(36), nullable=False),
    Column("name", String(255), nullable=False),
    Column("color", String(50), nullable=False, default="#808080"),
    Column("description", Text),
    Column("created_at", DateTime, nullable=False),
    UniqueConstraint("owner_id", "name", name="uq_dataset_tags_owner_name"),
)


class DatasetTagRepositoryAdapter(DatasetTagRepository):
    """标签仓储实现。SQLAlchemy Core Table 自动适配 MySQL / SQLite。"""

    _COLUMNS = "id, owner_id, name, color, description, created_at"

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
                s.execute(
                    text(
                        "CREATE UNIQUE INDEX IF NOT EXISTS uq_dataset_tags_owner_name "
                        "ON dataset_tags (owner_id, name)"
                    )
                )
                s.commit()
            except Exception:
                s.rollback()
                _logger.exception("Failed to ensure tag unique index")

    # ── DatasetTagRepository 实现 ─────────────────────────────

    def create(self, tag: DatasetTag) -> None:
        with self._session() as session:
            session.execute(
                text(
                    "INSERT INTO dataset_tags "
                    "(id, owner_id, name, color, description, created_at) "
                    "VALUES (:id, :owner_id, :name, :color, :description, :created_at)"
                ),
                {
                    "id": str(tag.id),
                    "owner_id": str(tag.owner_id),
                    "name": tag.name,
                    "color": tag.color,
                    "description": tag.description,
                    "created_at": datetime.now(),
                },
            )
            session.commit()

    def check_duplicate(self, tag: DatasetTag) -> None:
        """检查同用户下是否存在同名标签，存在则抛出 ValueError。"""
        existing = self.find_by_name(tag.owner_id, tag.name)
        if existing is not None and existing.id != tag.id:
            raise ValueError(f"Tag name already exists for this user: {tag.name}")

    def find_by_id(self, tag_id: uuid.UUID) -> DatasetTag | None:
        with self._session() as session:
            row = session.execute(
                text(f"SELECT {self._COLUMNS} FROM dataset_tags WHERE id = :id"),
                {"id": str(tag_id)},
            ).fetchone()
            if row is None:
                return None
            return self._row_to_tag(row)

    def find_by_name(self, owner_id: uuid.UUID, name: str) -> DatasetTag | None:
        with self._session() as session:
            row = session.execute(
                text(
                    f"SELECT {self._COLUMNS} FROM dataset_tags "
                    "WHERE owner_id = :owner_id AND name = :name"
                ),
                {"owner_id": str(owner_id), "name": name},
            ).fetchone()
            if row is None:
                return None
            return self._row_to_tag(row)

    def find_by_owner(self, owner_id: uuid.UUID) -> list[DatasetTag]:
        with self._session() as session:
            rows = session.execute(
                text(
                    f"SELECT {self._COLUMNS} FROM dataset_tags "
                    "WHERE owner_id = :owner_id ORDER BY id DESC"
                ),
                {"owner_id": str(owner_id)},
            ).fetchall()
            return [self._row_to_tag(r) for r in rows]

    def find_all(self) -> list[DatasetTag]:
        with self._session() as session:
            rows = session.execute(
                text(f"SELECT {self._COLUMNS} FROM dataset_tags ORDER BY id DESC"),
            ).fetchall()
            return [self._row_to_tag(r) for r in rows]

    def update_tag(self, tag_id: uuid.UUID, tag: DatasetTag) -> None:
        with self._session() as session:
            result = cast(CursorResult, session.execute(
                text(
                    "UPDATE dataset_tags SET "
                    "owner_id = :owner_id, name = :name, color = :color, "
                    "description = :description "
                    "WHERE id = :id"
                ),
                {
                    "id": str(tag_id),
                    "owner_id": str(tag.owner_id),
                    "name": tag.name,
                    "color": tag.color,
                    "description": tag.description,
                },
            ))
            if result.rowcount == 0:
                raise ValueError(f"Tag not found: {tag_id}")
            session.commit()

    def delete_tag(self, tag_id: uuid.UUID) -> None:
        with self._session() as session:
            result = cast(CursorResult, session.execute(
                text("DELETE FROM dataset_tags WHERE id = :id"),
                {"id": str(tag_id)},
            ))
            session.commit()
            if result.rowcount == 0:
                raise ValueError(f"Tag not found: {tag_id}")

    # ── 内部工具 ───────────────────────────────────────────────

    @staticmethod
    def _row_to_tag(row) -> DatasetTag:
        return DatasetTag(
            id=uuid.UUID(row.id),
            owner_id=uuid.UUID(row.owner_id),
            name=row.name,
            color=row.color,
            description=row.description or "",
            created_at=ensure_datetime(row.created_at),
        )
