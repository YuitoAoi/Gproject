"""数据集仓储实现 —— 通过 SQLAlchemy 自动适配 MySQL / SQLite。"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import List, Optional, cast

from sqlalchemy import Column, DateTime, Integer, MetaData, String, Table, Text, text
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session

from src.adapters.repositories._utils import ensure_datetime
from src.core.dataset import Dataset, DatasetMeta
from src.services.interfaces.dataset_repository import DatasetRepository
from src.services.interfaces.db_conn import DatabaseConnection

_logger = logging.getLogger(__name__)

_metadata = MetaData()

_dataset_table = Table(
    "datasets",
    _metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("owner_id", Integer, nullable=False, default=0),
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
                    "CREATE INDEX idx_datasets_owner_id ON datasets (owner_id)",
                    "CREATE INDEX idx_datasets_status ON datasets (status)",
                ]:
                    s.execute(text(idx_def))
                s.commit()
            except Exception as e:
                s.rollback()
                if "Duplicate key name" in str(e) or "1061" in str(e):
                    return
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

    def create(self, dataset: Dataset) -> Optional[Exception]:
        try:
            with self._session() as session:
                result = session.execute(
                    text(
                        "INSERT INTO datasets "
                        "(owner_id, name, description, meta, status, tag_ids, created_at, updated_at) "
                        "VALUES (:owner_id, :name, :desc, :meta, :status, :tag_ids, :created_at, :updated_at)"
                    ),
                    {
                        "owner_id": dataset.owner_id,
                        "name": dataset.name,
                        "desc": dataset.desc,
                        "meta": dataset.meta.to_json(),
                        "status": dataset.status,
                        "tag_ids": json.dumps(dataset.tag_ids),
                        "created_at": dataset.created_at,
                        "updated_at": dataset.updated_at,
                    },
                )
                session.commit()
                dataset.id = result.lastrowid
                return None
        except Exception as exc:
            return exc

    def find_by_id(self, id: int) -> Optional[Dataset]:
        try:
            with self._session() as session:
                row = session.execute(
                    text(f"SELECT {self._COLUMNS} FROM datasets WHERE id = :id"),
                    {"id": id},
                ).fetchone()
                if row is None:
                    return None
                return self._row_to_dataset(row)
        except Exception:
            _logger.exception("Failed to find dataset by id=%s", id)
            return None

    def find_by_owner(self, owner_id: int) -> List[Dataset]:
        try:
            with self._session() as session:
                rows = session.execute(
                    text(
                        f"SELECT {self._COLUMNS} FROM datasets "
                        "WHERE owner_id = :owner_id ORDER BY id DESC"
                    ),
                    {"owner_id": owner_id},
                ).fetchall()
                return [self._row_to_dataset(r) for r in rows]
        except Exception:
            _logger.exception("Failed to find datasets by owner_id=%s", owner_id)
            return []

    def find_all(self) -> List[Dataset]:
        try:
            with self._session() as session:
                rows = session.execute(
                    text(f"SELECT {self._COLUMNS} FROM datasets ORDER BY id DESC"),
                ).fetchall()
                return [self._row_to_dataset(r) for r in rows]
        except Exception:
            _logger.exception("Failed to find all datasets")
            return []

    def exists(self, id: int) -> bool:
        try:
            with self._session() as session:
                r = session.execute(
                    text("SELECT 1 FROM datasets WHERE id = :id"),
                    {"id": id},
                ).fetchone()
                return r is not None
        except Exception:
            _logger.exception("Failed to check dataset existence id=%s", id)
            return False

    def update(self, id: int, dataset: Dataset) -> Optional[Exception]:
        try:
            with self._session() as session:
                result = cast(
                    CursorResult,
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
                            "id": id,
                            "owner_id": dataset.owner_id,
                            "name": dataset.name,
                            "desc": dataset.desc,
                            "meta": dataset.meta.to_json(),
                            "status": dataset.status,
                            "tag_ids": json.dumps(dataset.tag_ids),
                            "created_at": dataset.created_at,
                            "updated_at": dataset.updated_at,
                        },
                    ),
                )
                session.commit()
                if result.rowcount == 0:
                    return ValueError(f"Dataset not found: {id}")
                return None
        except Exception as exc:
            return exc

    def remove(self, id: int) -> Optional[Exception]:
        try:
            dataset = self.find_by_id(id)
            if dataset is None:
                return ValueError(f"Dataset not found: {id}")
            with self._session() as session:
                session.execute(
                    text("DELETE FROM datasets WHERE id = :id"),
                    {"id": id},
                )
                session.commit()
            return None
        except Exception as exc:
            return exc

    def remove_batch(self, ids: List[int]) -> Optional[List[Exception]]:
        if not ids:
            return None
        try:
            with self._session() as session:
                placeholders = ",".join(f":id_{i}" for i in range(len(ids)))
                params = {f"id_{i}": id_ for i, id_ in enumerate(ids)}
                session.execute(
                    text(f"DELETE FROM datasets WHERE id IN ({placeholders})"),
                    params,
                )
                session.commit()
            return None
        except Exception as exc:
            return [exc]

    def count_by_owner_and_date(
        self, owner_id: int, date: datetime, field: str
    ) -> int:
        if field not in ("created_at", "updated_at"):
            return 0
        try:
            with self._session() as session:
                row = session.execute(
                    text(
                        "SELECT COUNT(*) FROM datasets "
                        "WHERE owner_id = :owner_id "
                        f"AND DATE({field}) = DATE(:date)"
                    ),
                    {"owner_id": owner_id, "date": date},
                ).fetchone()
                return row[0] if row else 0
        except Exception:
            _logger.exception("Failed to count datasets by owner and date")
            return 0

    def count_modified_today(self, owner_id: int, today: datetime) -> int:
        try:
            with self._session() as session:
                row = session.execute(
                    text(
                        "SELECT COUNT(*) FROM datasets "
                        "WHERE owner_id = :owner_id "
                        "AND DATE(updated_at) = DATE(:today) "
                        "AND DATE(created_at) < DATE(:today)"
                    ),
                    {"owner_id": owner_id, "today": today},
                ).fetchone()
                return row[0] if row else 0
        except Exception:
            _logger.exception("Failed to count modified today")
            return 0

    # ── 内部工具 ───────────────────────────────────────────────

    @staticmethod
    def _row_to_dataset(row) -> Dataset:
        meta_raw = row.meta
        if isinstance(meta_raw, str):
            meta = DatasetMeta.from_json(meta_raw)
        else:
            meta = DatasetMeta.from_dict(meta_raw)

        tag_ids_raw = row.tag_ids
        if isinstance(tag_ids_raw, str):
            tag_ids = json.loads(tag_ids_raw) if tag_ids_raw else []
        elif isinstance(tag_ids_raw, list):
            tag_ids = tag_ids_raw
        else:
            tag_ids = []

        return Dataset(
            id=row.id,
            owner_id=row.owner_id,
            name=row.name,
            desc=row.description,
            meta=meta,
            status=row.status or 0,
            tag_ids=tag_ids,
            created_at=ensure_datetime(row.created_at),
            updated_at=ensure_datetime(row.updated_at),
        )
