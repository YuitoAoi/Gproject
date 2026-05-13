# ruff: noqa: RUF003
"""任务仓储实现 —— SQLAlchemy Core Table。"""

from __future__ import annotations

import logging

from sqlalchemy import Column, DateTime, Float, Integer, MetaData, String, Table, Text, text
from src.adapters.repositories._utils import ensure_datetime
from src.core.task_record import TaskRecord
from src.services.interfaces.db_conn import DatabaseConnection

_logger = logging.getLogger(__name__)

_metadata = MetaData()

_tasks_table = Table(
    "tasks",
    _metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("owner_id", Integer, nullable=False),
    Column("task_name", String(255), nullable=False),
    Column("task_type", String(32), nullable=False, default="cleaning"),
    Column("status", String(16), nullable=False, default="pending"),
    Column("progress", Float, nullable=False, default=0.0),
    Column("phase", String(64), default=""),
    Column("config", Text, nullable=False, default="{}"),
    Column("created_at", DateTime, nullable=False),
    Column("updated_at", DateTime, nullable=False),
)


class TaskRepository:
    """任务仓储实现。SQLAlchemy Core Table 自动适配 MySQL / SQLite。"""

    _COLUMNS = "id, owner_id, task_name, task_type, status, progress, phase, config, created_at, updated_at"

    def __init__(self, connection: DatabaseConnection) -> None:
        self._conn = connection

    def init_table(self) -> None:
        self._conn.start()
        assert self._conn.engine is not None
        _metadata.create_all(self._conn.engine)

    def insert(self, task: TaskRecord) -> Exception | None:
        try:
            with self._conn.new_session() as session:
                result = session.execute(
                    text(
                        "INSERT INTO tasks "
                        "(owner_id, task_name, task_type, status, progress, phase, config, created_at, updated_at) "
                        "VALUES (:owner_id, :task_name, :task_type, :status, :progress, :phase, :config, :created_at, :updated_at)"
                    ),
                    {
                        "owner_id": task.owner_id,
                        "task_name": task.task_name,
                        "task_type": task.task_type,
                        "status": task.status,
                        "progress": task.progress,
                        "phase": task.phase,
                        "config": task.config,
                        "created_at": task.created_at,
                        "updated_at": task.updated_at,
                    },
                )
                # 获取自增 ID（在 commit 之前，cursor 仍然有效）
                last_id = result.lastrowid
                if not last_id:
                    # fallback: 通过 LAST_INSERT_ID() 获取
                    row = session.execute(text("SELECT LAST_INSERT_ID()")).fetchone()
                    last_id = row[0] if row else None
                session.commit()
                # 回填自增 ID
                if last_id:
                    task.id = last_id
                return None
        except Exception as exc:
            _logger.exception("Failed to insert task")
            return exc

    def find_by_id(self, id: int) -> TaskRecord | None:
        try:
            with self._conn.new_session() as session:
                row = session.execute(
                    text(f"SELECT {self._COLUMNS} FROM tasks WHERE id = :id"),
                    {"id": id},
                ).fetchone()
                if row is None:
                    return None
                return self._row_to_task(row)
        except Exception:
            _logger.exception("Failed to find task by id=%s", id)
            return None

    def find_by_config_job_id(self, owner_id: int, job_id: str) -> TaskRecord | None:
        try:
            with self._conn.new_session() as session:
                row = session.execute(
                    text(
                        f"SELECT {self._COLUMNS} FROM tasks "
                        "WHERE owner_id = :owner_id AND config LIKE :job_id ORDER BY id DESC LIMIT 1"
                    ),
                    {"owner_id": owner_id, "job_id": f"%{job_id}%"},
                ).fetchone()
                if row is None:
                    return None
                return self._row_to_task(row)
        except Exception:
            _logger.exception("Failed to find task by config job_id=%s", job_id)
            return None

    def find_by_owner(self, owner_id: int, status: str | None = None) -> list[TaskRecord]:
        try:
            with self._conn.new_session() as session:
                if status:
                    rows = session.execute(
                        text(
                            f"SELECT {self._COLUMNS} FROM tasks "
                            "WHERE owner_id = :owner_id AND status = :status ORDER BY id DESC"
                        ),
                        {"owner_id": owner_id, "status": status},
                    ).fetchall()
                else:
                    rows = session.execute(
                        text(f"SELECT {self._COLUMNS} FROM tasks WHERE owner_id = :owner_id ORDER BY id DESC"),
                        {"owner_id": owner_id},
                    ).fetchall()
                return [self._row_to_task(r) for r in rows]
        except Exception:
            _logger.exception("Failed to find tasks by owner_id=%s", owner_id)
            return []

    def find_by_owner_paged(
        self, owner_id: int, page: int, page_size: int, status: str | None = None
    ) -> tuple[list[TaskRecord], int]:
        try:
            offset = (page - 1) * page_size
            with self._conn.new_session() as session:
                if status:
                    count_row = session.execute(
                        text("SELECT COUNT(*) FROM tasks WHERE owner_id = :owner_id AND status = :status"),
                        {"owner_id": owner_id, "status": status},
                    ).fetchone()
                    rows = session.execute(
                        text(
                            f"SELECT {self._COLUMNS} FROM tasks "
                            "WHERE owner_id = :owner_id AND status = :status ORDER BY id DESC LIMIT :limit OFFSET :offset"
                        ),
                        {"owner_id": owner_id, "status": status, "limit": page_size, "offset": offset},
                    ).fetchall()
                else:
                    count_row = session.execute(
                        text("SELECT COUNT(*) FROM tasks WHERE owner_id = :owner_id"),
                        {"owner_id": owner_id},
                    ).fetchone()
                    rows = session.execute(
                        text(
                            f"SELECT {self._COLUMNS} FROM tasks "
                            "WHERE owner_id = :owner_id ORDER BY id DESC LIMIT :limit OFFSET :offset"
                        ),
                        {"owner_id": owner_id, "limit": page_size, "offset": offset},
                    ).fetchall()
                total = count_row[0] if count_row else 0
                return [self._row_to_task(r) for r in rows], total
        except Exception:
            _logger.exception("Failed to find tasks paged for owner_id=%s", owner_id)
            return [], 0

    def find_by_job_id(self, job_id: str) -> TaskRecord | None:
        try:
            with self._conn.new_session() as session:
                row = session.execute(
                    text(f"SELECT {self._COLUMNS} FROM tasks WHERE config LIKE :job_id ORDER BY id DESC LIMIT 1"),
                    {"job_id": f"%{job_id}%"},
                ).fetchone()
                if row is None:
                    return None
                return self._row_to_task(row)
        except Exception:
            _logger.exception("Failed to find task by job_id=%s", job_id)
            return None

    def update(self, id: int, task: TaskRecord) -> Exception | None:
        try:
            with self._conn.new_session() as session:
                session.execute(
                    text(
                        "UPDATE tasks SET "
                        "status = :status, progress = :progress, phase = :phase, "
                        "config = :config, updated_at = :updated_at "
                        "WHERE id = :id"
                    ),
                    {
                        "id": id,
                        "status": task.status,
                        "progress": task.progress,
                        "phase": task.phase,
                        "config": task.config,
                        "updated_at": task.updated_at,
                    },
                )
                session.commit()
                return None
        except Exception as exc:
            _logger.exception("Failed to update task id=%s", id)
            return exc

    def remove(self, id: int) -> Exception | None:
        try:
            with self._conn.new_session() as session:
                session.execute(
                    text("DELETE FROM tasks WHERE id = :id"),
                    {"id": id},
                )
                session.commit()
                return None
        except Exception as exc:
            _logger.exception("Failed to delete task id=%s", id)
            return exc

    def remove_by_config_dataset_id(self, owner_id: int, dataset_id: int) -> Exception | None:
        """删除 config 中包含指定 dataset_id 的所有任务记录。"""
        try:
            with self._conn.new_session() as session:
                pattern = f'%"dataset_id": {dataset_id}%'
                session.execute(
                    text("DELETE FROM tasks WHERE owner_id = :owner_id AND config LIKE :pattern"),
                    {"owner_id": owner_id, "pattern": pattern},
                )
                session.commit()
                return None
        except Exception as exc:
            _logger.exception(
                "Failed to delete tasks by dataset_id=%s for owner=%s",
                dataset_id,
                owner_id,
            )
            return exc

    @staticmethod
    def _row_to_task(row) -> TaskRecord:
        return TaskRecord(
            id=row.id,
            owner_id=row.owner_id,
            task_name=row.task_name,
            task_type=row.task_type,
            status=row.status,
            progress=row.progress or 0.0,
            phase=row.phase or "",
            config=row.config or "{}",
            created_at=ensure_datetime(row.created_at),
            updated_at=ensure_datetime(row.updated_at),
        )
