from __future__ import annotations

import json
from typing import List, Optional, cast
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session

from src.core.dataset import Dataset, DatasetMeta
from src.services.interfaces.dataset_repository import DatasetRepository
from src.services.interfaces.db_conn import DatabaseConnection


class MysqlDatasetRepository(DatasetRepository):
    """基于 SQLAlchemy + MySQL 的数据集仓储实现。

    meta 嵌套对象以 JSON 列存储，tag_ids 以 JSON 数组存储。
    所有写方法返回 Optional[Exception]：成功返回 None，失败返回异常对象。
    """

    _COLUMNS = ("id, owner_id, name, description, meta, status, tag_ids, "
                "created_at, updated_at")

    def __init__(self, connection: DatabaseConnection) -> None:
        self._conn = connection

    def _session(self) -> Session:
        return cast(Session, self._conn.new_session())

    # ── 表初始化 ──────────────────────────────────────────────

    def init_table(self) -> None:
        """确保 datasets 表结构与实体匹配。缺失列自动补齐。"""
        with self._session() as s:
            s.execute(text("""
                CREATE TABLE IF NOT EXISTS datasets (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    owner_id INT NOT NULL DEFAULT 0,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    meta JSON NOT NULL,
                    status INT DEFAULT 0,
                    tag_ids JSON,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """))
            s.commit()

            for col, col_def in [
                ("owner_id", "INT NOT NULL DEFAULT 0"),
                ("description", "TEXT"),
                ("meta", "JSON NOT NULL"),
                ("tag_ids", "JSON"),
            ]:
                try:
                    s.execute(text(
                        f"ALTER TABLE datasets ADD COLUMN {col} {col_def}"
                    ))
                    s.commit()
                except Exception:
                    s.rollback()
            # 旧表兼容：不再使用的列改为可空
            for old_col, old_type in [
                ("file_path", "VARCHAR(500)"),
                ("format", "VARCHAR(20)"),
                ("file_size", "BIGINT"),
                ("total_records", "INT"),
            ]:
                try:
                    s.execute(text(
                        f"ALTER TABLE datasets MODIFY COLUMN {old_col} {old_type} NULL"
                    ))
                    s.commit()
                except Exception:
                    s.rollback()
                try:
                    s.execute(text(
                        f"ALTER TABLE datasets ADD COLUMN {col} {col_def}"
                    ))
                    s.commit()
                except Exception:
                    s.rollback()

    # ── DatasetRepository 实现 ─────────────────────────────────

    def create(self, dataset: Dataset) -> Optional[Exception]:
        try:
            with self._session() as session:
                session.execute(
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
                new_id = session.execute(text("SELECT LAST_INSERT_ID()")).scalar()
                dataset.id = new_id
                return None
        except Exception as exc:
            return exc

    def find(self, id: int) -> Optional[Dataset]:
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
            return None

    def find_all(self) -> List[Dataset]:
        try:
            with self._session() as session:
                rows = session.execute(
                    text(f"SELECT {self._COLUMNS} FROM datasets ORDER BY id DESC"),
                ).fetchall()
                return [self._row_to_dataset(r) for r in rows]
        except Exception:
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
            return False

    def update(self, id: int, dataset: Dataset) -> Optional[Exception]:
        try:
            with self._session() as session:
                result = cast(CursorResult, session.execute(
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
                ))
                session.commit()
                if result.rowcount == 0:
                    return ValueError(f"Dataset not found: {id}")
                return None
        except Exception as exc:
            return exc

    def remove(self, id: int) -> Optional[Exception]:
        try:
            dataset = self.find(id)
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
            created_at=_ensure_datetime(row.created_at),
            updated_at=_ensure_datetime(row.updated_at),
        )


def _ensure_datetime(value) -> datetime:
    if isinstance(value, datetime):
        return value
    if value is not None:
        return datetime.fromisoformat(str(value))
    return value
