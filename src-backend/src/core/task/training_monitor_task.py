# ruff: noqa: RUF003
"""Celery 任务：训练监控 —— 轮询 trainer_state.json，读取 GPU 状态，发布到 Redis PubSub。"""

from __future__ import annotations

import json
import logging
import os
import shutil
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
TRAINING_LOG_DIR = Path(config.TRAINING_LOG_DIR)

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
        channel = f"progress:{job_id}"
        r.publish(channel, json.dumps(data, ensure_ascii=False))
    except Exception as exc:
        _logger.warning("[Monitor] Redis publish failed for %s: %s", job_id, exc)


def _read_trainer_state(output_dir: Path) -> dict | None:
    """读取 trainer_state.json，返回最新一步的指标。"""
    state_file = output_dir / "trainer_state.json"
    if not state_file.exists():
        return None
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
        log_history = state.get("log_history", [])
        if not log_history:
            return None
        latest = log_history[-1]
        return {
            "current_step": latest.get("step", 0),
            "total_steps": state.get("max_steps", 0),
            "loss": latest.get("loss"),
            "eval_loss": latest.get("eval_loss"),
            "learning_rate": latest.get("learning_rate"),
            "epoch": state.get("epoch", 0),
        }
    except (json.JSONDecodeError, OSError) as exc:
        _logger.warning("[Monitor] 读取 trainer_state 失败: %s", exc)
        return None


def _read_gpu_status() -> dict | None:
    """读取所有 GPU 显存与温度。pynvml 不可用时返回 None。"""
    try:
        import pynvml

        pynvml.nvmlInit()
        device_count = pynvml.nvmlDeviceGetCount()
        gpu_info = []
        for i in range(device_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            gpu_info.append({
                "used_memory_mb": mem_info.used // (1024 * 1024),
                "total_memory_mb": mem_info.total // (1024 * 1024),
                "temperature": temp,
            })
        pynvml.nvmlShutdown()
        return {"gpu": gpu_info}
    except Exception:
        return None


def _is_process_alive(job_id: str) -> bool:
    """根据 pid 文件检查子进程是否存活。"""
    pid_path = JOB_DIR / job_id / "pid"
    if not pid_path.exists():
        return False
    try:
        pid = int(pid_path.read_text(encoding="utf-8").strip())
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        return False


def _terminate_process(job_id: str) -> bool:
    """向训练子进程发送终止信号（兼容 Windows）。"""
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
        _logger.warning("[Monitor] 无法终止进程 %s: %s", job_id, exc)
        return False


def _get_db_conn():
    """获取数据库连接。"""
    try:
        from src.db_connections import create_db_connection

        db_conn = create_db_connection(config.DATABASE_URL)
        db_conn.start()
        return db_conn
    except Exception as exc:
        _logger.warning("[Monitor] 无法连接数据库: %s", exc)
        return None


def _update_task_progress(task_id: int, progress: float, phase: str, db_conn=None) -> None:
    """更新 TaskRecord 进度和阶段。"""
    from src.adapters.repositories.task_repo import TaskRepository

    should_dispose = False
    if db_conn is None:
        db_conn = _get_db_conn()
        should_dispose = True

    if db_conn is None:
        return

    try:
        repo = TaskRepository(db_conn)
        repo.update_progress(task_id, progress, phase)
        _logger.debug("[Monitor] task_id=%s progress=%.2f phase=%s", task_id, progress, phase)
    except Exception as exc:
        _logger.warning("[Monitor] 更新 task_id=%s 进度失败: %s", task_id, exc)
    finally:
        if should_dispose and db_conn:
            try:
                db_conn.dispose()
            except Exception:
                pass


def _update_task_status(task_id: int, status: str, db_conn=None) -> None:
    """更新 TaskRecord 状态。"""
    from src.adapters.repositories.task_repo import TaskRepository

    should_dispose = False
    if db_conn is None:
        db_conn = _get_db_conn()
        should_dispose = True

    if db_conn is None:
        return

    try:
        repo = TaskRepository(db_conn)
        repo.update_status(task_id, status)
        _logger.info("[Monitor] task_id=%s 状态已更新为 %s", task_id, status)
    except Exception as exc:
        _logger.warning("[Monitor] 更新 task_id=%s 状态失败: %s", task_id, exc)
    finally:
        if should_dispose and db_conn:
            try:
                db_conn.dispose()
            except Exception:
                pass


def _cleanup_training_logs(job_id: str) -> None:
    """清理训练任务目录及日志文件。"""
    try:
        # 清理 job 目录（含 config.json、pid、train.log、output/）
        job_dir = JOB_DIR / job_id
        if job_dir.exists():
            shutil.rmtree(job_dir)
            _logger.info("[Monitor] 清理训练任务目录: %s", job_dir)

        # 清理独立的训练日志目录（如果有）
        log_dir = TRAINING_LOG_DIR / job_id
        if log_dir.exists():
            shutil.rmtree(log_dir)
            _logger.info("[Monitor] 清理训练日志目录: %s", log_dir)
    except Exception as exc:
        _logger.warning("[Monitor] 清理训练日志失败: %s", exc)


@celery_client.task(bind=True, name="training.monitor", max_retries=0)
def monitor_training_job(self, job_id: str, task_id: int) -> dict:
    """Celery 监控任务：轮询训练进度，发布 Redis 消息，进程结束后更新状态。

    Args:
        job_id: LlamaFactoryTrainingClient 生成的任务 ID（train_xxx）
        task_id: TaskRecord 数据库主键
    """
    _logger.info("[Monitor] 启动训练监控: job_id=%s, task_id=%s", job_id, task_id)

    output_dir = JOB_DIR / job_id / "output"
    last_step = -1
    consecutive_missing = 0

    # 初始状态
    _publish(job_id, {"status": "running", "progress": 0.0, "stage": "训练启动中", "message": "等待训练进程初始化..."})

    while True:
        # 检查进程是否结束
        if not _is_process_alive(job_id):
            _logger.info("[Monitor] 训练进程已结束: job_id=%s", job_id)
            break

        # 读取 trainer_state
        state = _read_trainer_state(output_dir)

        if state is not None:
            consecutive_missing = 0
            current_step = state.get("current_step", 0)
            total_steps = state.get("total_steps", 0)

            # 仅当 step 有更新时发布消息，减少 Redis 流量
            if current_step != last_step:
                last_step = current_step
                progress = current_step / total_steps if total_steps > 0 else 0.0
                stage = "Supervised Fine-Tuning"

                msg = {
                    "status": "running",
                    "progress": progress,
                    "stage": stage,
                    "message": f"Step {current_step}/{total_steps}",
                    "current_step": current_step,
                    "total_steps": total_steps,
                    "loss": state.get("loss"),
                    "eval_loss": state.get("eval_loss"),
                    "learning_rate": state.get("learning_rate"),
                    "epoch": state.get("epoch"),
                }

                # 附加 GPU 信息（所有卡）
                gpu_info = _read_gpu_status()
                if gpu_info:
                    msg["gpu"] = gpu_info["gpu"]

                _publish(job_id, msg)

                # 更新数据库进度和阶段
                _update_task_progress(task_id, progress, stage)
        else:
            consecutive_missing += 1
            if consecutive_missing >= 3:
                _publish(job_id, {
                    "status": "running",
                    "progress": 0.0,
                    "stage": "等待训练数据",
                    "message": "trainer_state.json 尚未生成，训练可能仍在初始化..."
                })

        time.sleep(POLL_INTERVAL)

    # 进程结束后，读取最终状态
    final_state = _read_trainer_state(output_dir)
    if final_state is not None and final_state.get("loss") is not None:
        final_status = "done"
        final_msg = {
            "status": "done",
            "progress": 1.0,
            "stage": "训练完成",
            "message": "训练任务已完成，请前往任务详情查看最终结果",
            "final_loss": final_state.get("loss"),
            "final_eval_loss": final_state.get("eval_loss"),
        }
    else:
        final_status = "failed"
        final_msg = {
            "status": "failed",
            "progress": 0.0,
            "stage": "训练异常",
            "message": "训练进程已退出但未找到完整训练记录",
        }

    _publish(job_id, final_msg)
    _update_task_status(task_id, final_status)

    _logger.info("[Monitor] 训练监控结束: job_id=%s, final_status=%s", job_id, final_status)
    return {"job_id": job_id, "task_id": task_id, "status": final_status}