"""GraphGen 监控任务 —— 轮询 + 回调 backend。"""
import json
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


def _publish_progress(job_id: str, stage: str, progress: float, message: str, status: str = ""):
    try:
        r = redis.Redis.from_url(config.REDIS_URL, decode_responses=True)
        r.publish(
            f"progress:{job_id}",
            json.dumps({
                "stage": stage,
                "progress": progress,
                "message": message,
                "status": status,
            }),
        )
        r.close()
    except Exception:
        pass


@celery_app.task(name="dataset.monitor_graphgen", bind=True, max_retries=0)
def monitor_graphgen_job(self, job_id: str, dataset_id: int) -> Dict[str, Any]:
    """轮询 GraphGen 直到完成/失败，HTTP 回调 backend 更新 status。"""
    _publish_progress(job_id, "monitoring", 0.0, f"开始监控 job={job_id}", "pending")

    gg_url = config.GRAPHGEN_API_URL.rstrip("/api/v1")
    deadline = time.time() + 15 * 60

    while time.time() < deadline:
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
            _publish_progress(job_id, stage, progress, f"GraphGen: {status}", status)

            if status in ("done", "failed"):
                _callback_backend(job_id, dataset_id, data)
                _publish_progress(job_id, status, 1.0, f"回调完成: {status}", status)
                return {"success": status == "done", "status": status}

        except Exception as exc:
            _publish_progress(job_id, "retry", 0,
                              f"GraphGen 不可达，30s 后重试: {exc}", "running")
            time.sleep(30)
            continue

        time.sleep(5)

    _callback_backend(job_id, dataset_id, {"status": "failed", "error": "timeout"})
    _publish_progress(job_id, "timeout", 0.0, "超时 (15 min)", "failed")
    return {"success": False, "status": "timeout"}


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
