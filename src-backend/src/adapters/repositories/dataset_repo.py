"""数据集仓储实现 —— 通过 SQLAlchemy 自动适配 MySQL / SQLite。"""

from __future__ import annotations

import uuid, logging
from msgspec import convert, json as msgspec_json
from typing import cast

from sqlalchemy import Column, DateTime, Integer, MetaData, String, Table, Text, text
from sqlalchemy.orm import Session

from src.adapters.repositories._utils import ensure_datetime
from src.core import Dataset, DatasetMeta
from src.services.interfaces.dataset_repository import DatasetRepository
from src.services.interfaces.db_conn import DatabaseConnection

_logger = logging.getLogger(__name__)

_metadata = MetaData()

_dataset_table = Table(
    "datasets",
    _metadata,
    Column("id", String(36), primary_key=True),
    Column("owner_id", String(36), nullable=False),
    Column("name", String(255), nullable=False),
    Column("description", Text),
    Column("meta", Text, nullable=False, default="{}"),
    Column("status", Integer, default=0),
    Column("tag_ids", Text, default="[]"),
    Column("created_at", DateTime, nullable=False),
    Column("updated_at", DateTime, nullable=False),
)


class DatasetRepositoryAdapter(DatasetRepository):
    """数据集仓储实现。SQLAlchemy Core Table 自动适配 MySQL / SQLite。"""

    _COLUMNS = (
        "id, owner_id, name, description, meta, status, tag_ids, "
        "created_at, updated_at"
    )

    def __init__(self, connection: DatabaseConnection) -> None:
        self._conn = connection

    def _session(self) -> Session:
        return cast(Session, self._conn.new_session())

    # ── 表初始化 ──────────────────────────────────────────────

    def init_table(self) -> None:
        self._conn.start()
        assert self._conn.engine is not None
        _metadata.create_all(self._conn.engine)

    # ── 索引管理 ───────────────────────────────────────────────

    def ensure_indexes(self) -> None:
        with self._session() as s:
            try:
                for idx_def in [
                    "CREATE INDEX IF NOT EXISTS idx_datasets_owner_id ON datasets (owner_id)",
                    "CREATE INDEX IF NOT EXISTS idx_datasets_status ON datasets (status)",
                ]:
                    s.execute(text(idx_def))
                s.commit()
            except Exception:
                s.rollback()
                _logger.exception("Failed to ensure dataset indexes")
                raise

    def drop_indexes(self) -> None:
        with self._session() as s:
            try:
                for idx_name in ["idx_datasets_owner_id", "idx_datasets_status"]:
                    s.execute(text(f"DROP INDEX IF EXISTS {idx_name}"))
                s.commit()
            except Exception:
                s.rollback()
                _logger.exception("Failed to drop dataset indexes")
                raise

    # ── DatasetRepository 实现 ─────────────────────────────────

    def create(self, dataset: Dataset) -> None:
        with self._session() as session:
            session.execute(
                text(
                    "INSERT INTO datasets "
                    "(id, owner_id, name, description, meta, status, tag_ids, created_at, updated_at) "
                    "VALUES (:id, :owner_id, :name, :desc, :meta, :status, :tag_ids, :created_at, :updated_at)"
                ),
                {
                    "id": str(dataset.id),
                    "owner_id": str(dataset.owner_id),
                    "name": dataset.name,
                    "desc": dataset.desc,
                    "meta": dataset.meta.to_json(),
                    "status": dataset.status,
                    "tag_ids": msgspec_json.encode([str(t) for t in dataset.tag_ids]),
                    "created_at": dataset.created_at,
                    "updated_at": dataset.updated_at,
                },
            )
            session.commit()

    def find_by_id(self, id: uuid.UUID) -> Dataset | None:
        with self._session() as session:
            row = session.execute(
                text(f"SELECT {self._COLUMNS} FROM datasets WHERE id = :id"),
                {"id": str(id)},
            ).fetchone()
            if row is None:
                return None
            return self._row_to_dataset(row)

    def find_by_owner(self, owner_id: uuid.UUID) -> list[Dataset]:
        with self._session() as session:
            rows = session.execute(
                text(
                    f"SELECT {self._COLUMNS} FROM datasets "
                    "WHERE owner_id = :owner_id ORDER BY id DESC"
                ),
                {"owner_id": str(owner_id)},
            ).fetchall()
            return [self._row_to_dataset(r) for r in rows]

    def find_all(self) -> list[Dataset]:
        with self._session() as session:
            rows = session.execute(
                text(f"SELECT {self._COLUMNS} FROM datasets ORDER BY id DESC"),
            ).fetchall()
            return [self._row_to_dataset(r) for r in rows]

    def exists(self, id: uuid.UUID) -> bool:
        with self._session() as session:
            r = session.execute(
                text("SELECT 1 FROM datasets WHERE id = :id"),
                {"id": str(id)},
            ).fetchone()
            return r is not None

    def update(self, id: uuid.UUID, dataset: Dataset) -> None:
        with self._session() as session:
            session.execute(
                text(
                    "UPDATE datasets SET "
                    "owner_id = :owner_id, "
                    "name = :name, description = :desc, meta = :meta, "
                    "status = :status, tag_ids = :tag_ids, "
                    "created_at = :created_at, updated_at = :updated_at "
                    "WHERE id = :id"
                ),
                {
                    "id": str(id),
                    "owner_id": str(dataset.owner_id),
                    "name": dataset.name,
                    "desc": dataset.desc,
                    "meta": dataset.meta.to_json(),
                    "status": dataset.status,
                    "tag_ids": msgspec_json.encode([str(t) for t in dataset.tag_ids]),
                    "created_at": dataset.created_at,
                    "updated_at": dataset.updated_at,
                },
            )
            session.commit()

    def remove(self, id: uuid.UUID) -> None:
        with self._session() as session:
            session.execute(
                text("DELETE FROM datasets WHERE id = :id"),
                {"id": str(id)},
            )
            session.commit()

    def remove_batch(self, ids: list[uuid.UUID]) -> list[Exception]:
        with self._session() as session:
            placeholders = ",".join(f":id_{i}" for i in range(len(ids)))
            params = {f"id_{i}": id_ for i, id_ in enumerate(ids)}
            session.execute(
                text(f"DELETE FROM datasets WHERE id IN ({placeholders})"),
                params,
            )
            session.commit()
        return []

    # ── 内部工具 ───────────────────────────────────────────────

    @staticmethod
    def _row_to_dataset(row) -> Dataset:
        from msgspec import json
        import uuid

        return Dataset(
            id=uuid.UUID(row.id),
            owner_id=uuid.UUID(row.owner_id),
            name=row.name,
            desc=row.description,
            meta=DatasetMeta.from_json(row.meta),
            status=row.status or 0,
            tag_ids=json.decode(row.tag_ids, type=list[uuid.UUID]),
            created_at=ensure_datetime(row.created_at),
            updated_at=ensure_datetime(row.updated_at),
        )
