# ruff: noqa: RUF003
"""Celery 任务：导出监控 —— 轮询导出进程状态，发布到 Redis PubSub。"""

from __future__ import annotations

import json
import logging
import os
import signal
import sys
import time
from pathlib import Path

import redis

from src.adapters.celery_client import celery_client
from src.core.config import config

_logger = logging.getLogger(__name__)

REDIS_URL = config.REDIS_URL
JOB_DIR = Path(config.LLAMAFACTORY_JOB_DIR)
POLL_INTERVAL = config.LLAMAFACTORY_POLL_INTERVAL_SECONDS

_pubsub_client: redis.Redis | None = None

# 导出阶段关键词 → 进度估算
_STAGE_HINTS = [
    ("Merging", 0.1),
    ("Loading", 0.15),
    ("Quantizing", 0.4),
    ("Exporting", 0.6),
    ("Converting", 0.7),
    ("Saving", 0.85),
    ("Complete", 1.0),
]


def _get_redis() -> redis.Redis:
    global _pubsub_client
    if _pubsub_client is None:
        _pubsub_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    return _pubsub_client


def _publish(job_id: str, data: dict) -> None:
    try:
        r = _get_redis()
        r.publish(f"progress:{job_id}", json.dumps(data, ensure_ascii=False))
    except Exception as exc:
        _logger.warning("[ExportMonitor] Redis publish failed: %s", exc)


def _is_process_alive(job_id: str) -> bool:
    pid_path = JOB_DIR / job_id / "pid"
    if not pid_path.exists():
        return False
    try:
        pid = int(pid_path.read_text(encoding="utf-8").strip())
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        return False


def _read_export_log(log_file: Path) -> list[str]:
    if not log_file.exists():
        return []
    try:
        return log_file.read_text(encoding="utf-8").splitlines()
    except Exception:
        return []


def _detect_stage(lines: list[str]) -> tuple[str, float]:
    """从日志行中检测导出阶段和进度。"""
    for line in reversed(lines):
        lower = line.lower()
        for hint, progress in _STAGE_HINTS:
            if hint.lower() in lower:
                return hint, progress
    return "准备中", 0.0


def _terminate_process(job_id: str) -> bool:
    pid_path = JOB_DIR / job_id / "pid"
    if not pid_path.exists():
        return False
    try:
        pid = int(pid_path.read_text(encoding="utf-8").strip())
        if sys.platform == "win32":
            import ctypes

            kernel32 = ctypes.windll.kernel32
            PROCESS_TERMINATE = 1
            handle = kernel32.OpenProcess(PROCESS_TERMINATE, False, pid)
            if handle:
                kernel32.TerminateProcess(handle, 0)
                kernel32.CloseHandle(handle)
                return True
            return False
        else:
            os.kill(pid, signal.SIGTERM)
            return True
    except (OSError, ValueError, ImportError) as exc:
        _logger.warning("[ExportMonitor] 无法终止进程 %s: %s", job_id, exc)
        return False


def _get_db_conn():
    try:
        from src.db_connections import create_db_connection

        db_conn = create_db_connection(config.DATABASE_URL)
        db_conn.start()
        return db_conn
    except Exception as exc:
        _logger.warning("[ExportMonitor] 无法连接数据库: %s", exc)
        return None


def _update_task_status(task_id: int, status: str) -> None:
    from src.adapters.repositories.task_repo import TaskRepository

    db_conn = _get_db_conn()
    if db_conn is None:
        return
    try:
        repo = TaskRepository(db_conn)
        repo.update_status(task_id, status)
        _logger.info("[ExportMonitor] task_id=%s 状态已更新为 %s", task_id, status)
    except Exception as exc:
        _logger.warning("[ExportMonitor] 更新 task_id=%s 状态失败: %s", task_id, exc)
    finally:
        try:
            db_conn.dispose()
        except Exception:
            pass


def _update_task_progress(task_id: int, progress: float, phase: str) -> None:
    from src.adapters.repositories.task_repo import TaskRepository

    db_conn = _get_db_conn()
    if db_conn is None:
        return
    try:
        repo = TaskRepository(db_conn)
        repo.update_progress(task_id, progress, phase)
    except Exception as exc:
        _logger.warning("[ExportMonitor] 更新 task_id=%s 进度失败: %s", task_id, exc)
    finally:
        try:
            db_conn.dispose()
        except Exception:
            pass


@celery_client.task(bind=True, name="export.monitor", max_retries=0)
def monitor_export_job(self, job_id: str, task_id: int) -> dict:
    _logger.info("[ExportMonitor] 启动导出监控: job_id=%s, task_id=%s", job_id, task_id)

    job_dir = JOB_DIR / job_id
    log_file = job_dir / "export.log"

    _publish(job_id, {
        "status": "running",
        "progress": 0.0,
        "stage": "导出启动中",
        "message": "正在初始化导出进程...",
    })

    last_log_size = 0
    last_stage = "导出启动中"
    last_progress = 0.0

    while True:
        if not _is_process_alive(job_id):
            break

        if log_file.exists():
            current_size = log_file.stat().st_size
            if current_size > last_log_size:
                lines = _read_export_log(log_file)
                stage, progress = _detect_stage(lines)
                if stage != last_stage or progress != last_progress:
                    last_stage = stage
                    last_progress = progress
                    last_msg = lines[-1].strip()[:150] if lines else ""
                    _publish(job_id, {
                        "status": "running",
                        "progress": progress,
                        "stage": stage,
                        "message": last_msg,
                    })
                    _update_task_progress(task_id, progress, stage)
                last_log_size = current_size

        time.sleep(POLL_INTERVAL)

    # 进程结束后检查产物文件
    cfg_file = job_dir / "export_config.json"
    export_path = ""
    if cfg_file.exists():
        try:
            cfg = json.loads(cfg_file.read_text(encoding="utf-8"))
            export_path = cfg.get("export_path", "")
        except Exception:
            pass

    if export_path and os.path.exists(export_path):
        final_status = "done"
        file_size = os.path.getsize(export_path)
        final_msg = {
            "status": "done",
            "progress": 1.0,
            "stage": "导出完成",
            "message": f"导出成功: {os.path.basename(export_path)}",
            "export_path": export_path,
            "file_size": file_size,
        }
    else:
        lines = _read_export_log(log_file)
        last_line = lines[-1] if lines else ""
        final_status = "failed"
        final_msg = {
            "status": "failed",
            "progress": 0.0,
            "stage": "导出异常",
            "message": f"导出进程已结束但未找到产物文件。{last_line[:100]}",
        }

    _publish(job_id, final_msg)
    _update_task_status(task_id, final_status)
    _logger.info("[ExportMonitor] 导出监控结束: job_id=%s, status=%s", job_id, final_status)
    return {"job_id": job_id, "task_id": task_id, "status": final_status}