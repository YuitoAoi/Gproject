"""数据集日志仓储 —— SQLAlchemy Core Table。"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Integer, MetaData, String, Table, text
from sqlalchemy.orm import Session

from src.adapters.repositories._utils import ensure_datetime
from src.core.dataset_log import DatasetLog
from src.services.interfaces.db_conn import DatabaseConnection

_logger = logging.getLogger(__name__)

_metadata = MetaData()

_dataset_logs_table = Table(
    "dataset_logs",
    _metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("job_id", String(64), nullable=False),
    Column("dataset_id", Integer, nullable=False),
    Column("log_path", String(512), nullable=False),
    Column("created_at", DateTime, nullable=False),
)


class DatasetLogRepository:
    """数据集日志仓储实现。SQLAlchemy Core Table 自动适配 MySQL / SQLite。"""

    _COLUMNS = "id, job_id, dataset_id, log_path, created_at"

    def __init__(self, connection: DatabaseConnection) -> None:
        self._conn = connection

    def init_table(self) -> None:
        self._conn.start()
        assert self._conn.engine is not None
        _metadata.create_all(self._conn.engine)

    def insert(self, log: DatasetLog) -> Optional[Exception]:
        try:
            with self._conn.new_session() as session:
                session.execute(
                    text(
                        "INSERT INTO dataset_logs "
                        "(job_id, dataset_id, log_path, created_at) "
                        "VALUES (:job_id, :dataset_id, :log_path, :created_at)"
                    ),
                    {
                        "job_id": log.job_id,
                        "dataset_id": log.dataset_id,
                        "log_path": log.log_path,
                        "created_at": log.created_at,
                    },
                )
                session.commit()
                return None
        except Exception as exc:
            _logger.exception("Failed to insert dataset_log")
            return exc

    def find_by_job_id(self, job_id: str) -> Optional[DatasetLog]:
        try:
            with self._conn.new_session() as session:
                row = session.execute(
                    text(f"SELECT {self._COLUMNS} FROM dataset_logs WHERE job_id = :job_id"),
                    {"job_id": job_id},
                ).fetchone()
                if row is None:
                    return None
                return DatasetLog(
                    id=row.id,
                    job_id=row.job_id,
                    dataset_id=row.dataset_id,
                    log_path=row.log_path,
                    created_at=ensure_datetime(row.created_at),
                )
        except Exception:
            _logger.exception("Failed to find dataset_log by job_id=%s", job_id)
            return None
