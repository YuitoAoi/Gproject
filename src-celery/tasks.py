"""GraphGen 监控任务 —— 轮询 + 回调 backend + 写入日志文件。"""
import json
import os
import time
from typing import Any, Dict

import httpx
import redis

from config import config
from main import celery_app

_CALLBACK_URL = (
    f"http://{config.BACKEND_HOST}:{config.BACKEND_PORT}"
    f"/api/v1/dataset/process/callback"
)

_LOG_DIR = os.path.join("data", "logs", "dataset_logs")


def _get_log_path(job_id: str) -> str:
    return os.path.join(_LOG_DIR, f"{job_id}.log")


def _append_log(job_id: str, line: str) -> None:
    try:
        os.makedirs(_LOG_DIR, exist_ok=True)
        log_path = _get_log_path(job_id)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def _publish_progress(job_id: str, stage: str, progress: float, message: str, status: str = ""):
    try:
        r = redis.Redis.from_url(config.REDIS_URL, decode_responses=True)
        r.publish(
            f"progress:{job_id}",
            json.dumps({
                "type": "stage",
                "stage": stage,
                "progress": progress,
                "message": message,
                "status": status,
            }),
        )
        r.close()
    except Exception:
        pass


def _publish_log(job_id: str, line: str):
    _append_log(job_id, line)
    try:
        r = redis.Redis.from_url(config.REDIS_URL, decode_responses=True)
        r.publish(
            f"progress:{job_id}",
            json.dumps({
                "type": "engine_log",
                "line": line,
                "status": "running",
            }),
        )
        r.close()
    except Exception:
        pass


def _publish_heartbeat(job_id: str, status: str, progress: float):
    try:
        r = redis.Redis.from_url(config.REDIS_URL, decode_responses=True)
        r.publish(
            f"progress:{job_id}",
            json.dumps({
                "type": "heartbeat",
                "status": status,
                "progress": progress,
            }),
        )
        r.close()
    except Exception:
        pass


@celery_app.task(name="dataset.monitor_graphgen", bind=True, max_retries=0)
def monitor_graphgen_job(self, job_id: str, dataset_id: int) -> Dict[str, Any]:
    """轮询 GraphGen 直到完成/失败，HTTP 回调 backend 更新 status。"""
    _publish_progress(job_id, "monitoring", 0.0, f"开始监控 job={job_id}", "pending")

    log_offset = 0
    last_stage = None
    last_progress = -1
    heartbeat_count = 0

    while True:
        try:
            resp = httpx.get(
                f"{config.GRAPHGEN_API_URL}/jobs/{job_id}",
                timeout=10,
            )
            if resp.is_error:
                raise RuntimeError(f"GraphGen HTTP {resp.status_code}")

            data = resp.json()
            status = data.get("status")
            progress = data.get("progress", 0)
            stage = data.get("stage", status)

            heartbeat_count += 1
            if stage != last_stage or progress != last_progress:
                _publish_progress(job_id, stage, progress, f"GraphGen: {status}", status)
                last_stage = stage
                last_progress = progress
                heartbeat_count = 0
            elif heartbeat_count >= 6:
                _publish_heartbeat(job_id, status, progress)
                heartbeat_count = 0

            if status in ("done", "failed"):
                _callback_backend(job_id, dataset_id, data)
                _publish_progress(job_id, status, 1.0, f"回调完成: {status}", status)
                return {"success": status == "done", "status": status}

        except Exception as exc:
            _publish_progress(job_id, "retry", 0,
                              f"GraphGen 不可达，30s 后重试: {exc}", "running")
            time.sleep(30)
            continue

        try:
            log_resp = httpx.get(
                f"{config.GRAPHGEN_API_URL}/jobs/{job_id}/logs?offset={log_offset}",
                timeout=5,
            )
            if not log_resp.is_error:
                log_data = log_resp.json()
                for line in log_data.get("lines", []):
                    if any(skip in line for skip in ["progress_bar.py", "streaming_executor.py", "dataset.py:5344"]):
                        continue
                    _publish_log(job_id, line)
                log_offset = log_data.get("offset", log_offset)
        except Exception:
            pass

        time.sleep(5)


def _callback_backend(job_id: str, dataset_id: int, graphgen_result: dict) -> None:
    try:
        httpx.post(_CALLBACK_URL, json={
            "job_id": job_id,
            "dataset_id": dataset_id,
            "status": graphgen_result.get("status"),
            "output_path": graphgen_result.get("output_path"),
            "error": graphgen_result.get("error"),
        }, timeout=10)
    except Exception:
        pass
