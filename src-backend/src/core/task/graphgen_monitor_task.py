# ruff: noqa: RUF003
"""Celery 任务：GraphGen 数据清洗监控 —— 轮询 GraphGen API，发布 Redis 消息，更新任务阶段与日志文件。"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from pathlib import Path

import redis

from src.adapters.celery_client import celery_client
from src.core.config import config

_logger = logging.getLogger(__name__)

REDIS_URL = config.REDIS_URL
DATASET_LOG_DIR = Path(config.DATASET_LOG_DIR)
POLL_INTERVAL = config.LLAMAFACTORY_POLL_INTERVAL_SECONDS

_pubsub_client: redis.Redis | None = None


def _get_redis() -> redis.Redis:
    global _pubsub_client
    if _pubsub_client is None:
        _pubsub_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    return _pubsub_client


def _publish(job_id: str, data: dict) -> None:
    """发布消息到 Redis PubSub channel progress:{job_id}。"""
    try:
        r = _get_redis()
        r.publish(f"progress:{job_id}", json.dumps(data, ensure_ascii=False))
    except Exception as exc:
        _logger.warning("[GraphGenMonitor] Redis publish failed for %s: %s", job_id, exc)


def _get_db_conn():
    """获取数据库连接。"""
    try:
        from src.db_connections import create_db_connection

        db_conn = create_db_connection(config.DATABASE_URL)
        db_conn.start()
        return db_conn
    except Exception as exc:
        _logger.warning("[GraphGenMonitor] 无法连接数据库: %s", exc)
        return None


def _find_task_by_job_id(job_id: str) -> int | None:
    """通过 job_id 查找 TaskRecord 的 id。"""
    db_conn = _get_db_conn()
    if db_conn is None:
        return None
    try:
        from src.adapters.repositories.task_repo import TaskRepository

        repo = TaskRepository(db_conn)
        task = repo.find_by_job_id(job_id)
        return task.id if task else None
    except Exception as exc:
        _logger.warning("[GraphGenMonitor] 查找 task 失败: %s", exc)
        return None
    finally:
        try:
            db_conn.dispose()
        except Exception:
            pass


def _update_task_progress(task_id: int, progress: float, phase: str) -> None:
    """更新 TaskRecord 进度和阶段。"""
    from src.adapters.repositories.task_repo import TaskRepository

    db_conn = _get_db_conn()
    if db_conn is None:
        return
    try:
        repo = TaskRepository(db_conn)
        repo.update_progress(task_id, progress, phase)
        _logger.debug("[GraphGenMonitor] task_id=%s progress=%.2f phase=%s", task_id, progress, phase)
    except Exception as exc:
        _logger.warning("[GraphGenMonitor] 更新 task_id=%s 进度失败: %s", task_id, exc)
    finally:
        try:
            db_conn.dispose()
        except Exception:
            pass


def _update_task_status(task_id: int, status: str) -> None:
    """更新 TaskRecord 最终状态。"""
    from src.adapters.repositories.task_repo import TaskRepository

    db_conn = _get_db_conn()
    if db_conn is None:
        return
    try:
        repo = TaskRepository(db_conn)
        repo.update_status(task_id, status)
        _logger.info("[GraphGenMonitor] task_id=%s 状态已更新为 %s", task_id, status)
    except Exception as exc:
        _logger.warning("[GraphGenMonitor] 更新 task_id=%s 状态失败: %s", task_id, exc)
    finally:
        try:
            db_conn.dispose()
        except Exception:
            pass


def _append_log(log_file: Path, line: str) -> None:
    """追加一行到日志文件。"""
    if not log_file.parent.exists():
        log_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as exc:
        _logger.warning("[GraphGenMonitor] 写入日志失败: %s", exc)


# GraphGen API 阶段 → 前端 stage 标签
_STAGE_LABELS: dict[str, str] = {
    "pending": "等待调度",
    "running": "处理中",
    "chunking": "数据分块",
    "reading": "读取源数据",
    "processing": "数据处理",
    "generating": "生成结果",
    "saving": "保存产物",
    "done": "处理完成",
    "failed": "任务失败",
}


@celery_client.task(bind=True, name="dataset.monitor_graphgen", max_retries=0)
def monitor_graphgen_job(self, job_id: str, dataset_id: int) -> dict:
    """Celery 监控任务：轮询 GraphGen API 状态，发布 Redis 消息，更新任务阶段。

    Args:
        job_id: GraphGen API 返回的 job_id
        dataset_id: 数据集 ID（仅用于通过 config 中 job_id 关联定位 TaskRecord）
    """
    _logger.info("[GraphGenMonitor] 启动监控: job_id=%s, dataset_id=%s", job_id, dataset_id)

    log_file = DATASET_LOG_DIR / f"{job_id}.log"
    DATASET_LOG_DIR.mkdir(parents=True, exist_ok=True)

    _append_log(log_file, f"[{datetime.now().isoformat()}] [INFO] [GraphGenMonitor] 任务已启动, job_id={job_id}")

    # 通过 job_id 查找对应的 TaskRecord（清洗任务的 task.id）
    task_id = _find_task_by_job_id(job_id)
    if task_id is None:
        _logger.error("[GraphGenMonitor] 无法找到 job_id=%s 对应的 TaskRecord", job_id)
        _append_log(log_file, f"[{datetime.now().isoformat()}] [ERROR] [GraphGenMonitor] 未找到任务记录, job_id={job_id}")
        return {"job_id": job_id, "task_id": None, "dataset_id": dataset_id, "status": "failed"}

    _logger.info("[GraphGenMonitor] 关联 TaskRecord: task_id=%s", task_id)

    # 初始状态推送
    _publish(job_id, {
        "status": "running",
        "progress": 0.0,
        "stage": "等待调度",
        "message": "GraphGen 任务正在等待调度...",
    })
    _update_task_status(task_id, "running")

    last_status = ""
    last_stage = ""
    last_progress = 0.0

    while True:
        try:
            from src.adapters.graphgen_client import GraphGenClient

            client = GraphGenClient()
            resp = client.get_job(job_id)
            if resp.is_error:
                _logger.warning("[GraphGenMonitor] 查询 job_id=%s 失败: %s", job_id, resp.text)
                time.sleep(POLL_INTERVAL)
                continue

            data = resp.json()
        except Exception as exc:
            _logger.warning("[GraphGenMonitor] GraphGen API 调用失败: %s", exc)
            time.sleep(POLL_INTERVAL)
            continue

        status = data.get("status", "unknown")
        progress = float(data.get("progress", 0.0))
        stage_raw = data.get("stage", status)
        message = data.get("message", data.get("error", ""))
        output_path = data.get("output_path")

        stage = _STAGE_LABELS.get(stage_raw, stage_raw if stage_raw else "处理中")

        log_line = f"[{datetime.now().isoformat()}] [INFO] [{stage}] {message}"
        _append_log(log_file, log_line)

        if status != last_status or stage != last_stage or abs(progress - last_progress) > 0.01:
            last_status = status
            last_stage = stage
            last_progress = progress

            _publish(job_id, {
                "status": status,
                "progress": progress,
                "stage": stage,
                "message": message,
                "type": "engine_log",
                "line": log_line,
            })

            _update_task_progress(task_id, progress, stage)

        if status in ("done", "failed", "cancelled"):
            break

        time.sleep(POLL_INTERVAL)

    if status == "done":
        final_msg = f"数据清洗完成，产出路径: {output_path or '未知'}"
        _publish(job_id, {
            "status": "done",
            "progress": 1.0,
            "stage": "处理完成",
            "message": final_msg,
        })
        _update_task_status(task_id, "done")
        _append_log(log_file, f"[{datetime.now().isoformat()}] [INFO] [GraphGenMonitor] 任务完成, output={output_path}")
        _logger.info("[GraphGenMonitor] 任务完成: job_id=%s, output=%s", job_id, output_path)
    else:
        error_msg = message or "GraphGen 任务执行失败"
        _publish(job_id, {
            "status": status,
            "progress": 0.0,
            "stage": "任务失败",
            "message": error_msg,
        })
        _update_task_status(task_id, "failed")
        _append_log(log_file, f"[{datetime.now().isoformat()}] [ERROR] [GraphGenMonitor] 任务失败: {error_msg}")
        _logger.info("[GraphGenMonitor] 任务失败: job_id=%s, error=%s", job_id, error_msg)

    return {"job_id": job_id, "task_id": task_id, "dataset_id": dataset_id, "status": status}