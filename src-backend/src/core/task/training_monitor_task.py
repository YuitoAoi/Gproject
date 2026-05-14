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


def _find_best_checkpoint(output_dir: Path) -> str | None:
    """从 trainer_state.json 查找最佳检查点，回退到最新 checkpoint 目录。"""
    state_file = output_dir / "trainer_state.json"
    if state_file.exists():
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
            best = state.get("best_model_checkpoint")
            if best and os.path.exists(best):
                return best
        except Exception:
            pass
    # 回退：扫描 checkpoint-* 目录，取最大 step
    if output_dir.exists():
        checkpoints = sorted(
            [d for d in output_dir.iterdir() if d.is_dir() and d.name.startswith("checkpoint-")],
            key=lambda d: int(d.name.split("-")[-1]) if d.name.split("-")[-1].isdigit() else 0,
        )
        if checkpoints:
            return str(checkpoints[-1])
    return None


def _update_task_config(task_id: int, extra: dict) -> None:
    """将额外字段合并到 TaskRecord 的 config JSON 中。"""
    from src.adapters.repositories.task_repo import TaskRepository

    db_conn = _get_db_conn()
    if db_conn is None:
        return
    try:
        repo = TaskRepository(db_conn)
        repo.update_config(task_id, extra)
    except Exception as exc:
        _logger.warning("[Monitor] 更新 task_id=%s 配置失败: %s", task_id, exc)
    finally:
        try:
            db_conn.dispose()
        except Exception:
            pass


_EXPORT_STAGE_HINTS = [
    ("Merging", 0.10),
    ("Loading", 0.15),
    ("Quantizing", 0.40),
    ("Exporting", 0.60),
    ("Converting", 0.70),
    ("Saving", 0.85),
    ("Complete", 1.00),
]


def _run_export_phase(
    training_job_id: str,
    task_id: int,
    output_dir: Path,
    base_model: str,
    db_conn,
) -> str:
    """训练成功后自动导出最佳检查点的 GGUF 模型，内联监控循环。

    Returns:
        最终状态 "done" 或 "failed"。
    """
    from src.adapters.llamafactory_export_client import LlamaFactoryExportClient, ExportConfig

    # 查找最佳检查点
    adapter_path = _find_best_checkpoint(output_dir)
    if not adapter_path:
        _publish(training_job_id, {
            "status": "failed", "progress": 0.0,
            "phase": "exporting", "stage": "导出失败",
            "message": "训练完成但未找到可导出的检查点",
        })
        _update_task_status(task_id, "failed", db_conn)
        return "failed"

    # 发布阶段过渡消息
    _publish(training_job_id, {
        "status": "running", "progress": 0.0,
        "phase": "exporting", "stage": "准备导出",
        "message": "训练完成，正在准备GGUF导出...",
    })
    _update_task_progress(task_id, 0.0, "exporting", db_conn)

    # 提交导出
    export_client = LlamaFactoryExportClient()
    export_config = ExportConfig(
        base_model=base_model,
        adapter_path=adapter_path,
        export_format="gguf",
        quantization_method="q4_k_m",
    )
    result = export_client.submit_export(export_config)
    if not result.success:
        _publish(training_job_id, {
            "status": "failed", "progress": 0.0,
            "phase": "exporting", "stage": "导出失败",
            "message": f"导出启动失败: {result.error}",
        })
        _update_task_status(task_id, "failed", db_conn)
        return "failed"

    # 将导出信息写入 task config
    _update_task_config(task_id, {
        "export_job_id": result.job_id,
        "export_adapter_path": adapter_path,
        "export_path": result.export_path,
    })

    # 导出监控循环
    export_log_file = JOB_DIR / result.job_id / "export.log"
    last_log_size = 0
    last_stage = "准备导出"
    last_progress = 0.0

    while _is_process_alive(result.job_id):
        if export_log_file.exists():
            current_size = export_log_file.stat().st_size
            if current_size > last_log_size:
                try:
                    lines = export_log_file.read_text(encoding="utf-8").splitlines()
                except Exception:
                    lines = []
                # 从最新行开始检测阶段
                for line in reversed(lines):
                    lower = line.lower()
                    for hint, progress in _EXPORT_STAGE_HINTS:
                        if hint.lower() in lower:
                            if hint != last_stage or progress != last_progress:
                                last_stage = hint
                                last_progress = progress
                                last_msg = lines[-1].strip()[:200] if lines else ""
                                _publish(training_job_id, {
                                    "status": "running",
                                    "progress": progress,
                                    "phase": "exporting",
                                    "stage": hint,
                                    "message": last_msg,
                                })
                                _update_task_progress(task_id, progress, "exporting", db_conn)
                            break
                    else:
                        continue
                    break
                last_log_size = current_size
        time.sleep(POLL_INTERVAL)

    # 检查导出产物
    export_path = result.export_path
    if export_path and os.path.exists(export_path):
        file_size = os.path.getsize(export_path)
        _publish(training_job_id, {
            "status": "done", "progress": 1.0,
            "phase": "exporting", "stage": "导出完成",
            "message": f"GGUF导出成功: {os.path.basename(export_path)}",
            "export_path": export_path, "file_size": file_size,
        })
        _update_task_config(task_id, {"export_file_size": file_size})
        _update_task_progress(task_id, 1.0, "done", db_conn)
        _update_task_status(task_id, "done", db_conn)
        return "done"
    else:
        _publish(training_job_id, {
            "status": "failed", "progress": 0.0,
            "phase": "exporting", "stage": "导出异常",
            "message": "导出进程已结束但未找到产物文件",
        })
        _update_task_status(task_id, "failed", db_conn)
        return "failed"


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
        # 训练成功 — 发布过渡消息，然后启动自动导出
        _publish(job_id, {
            "status": "running",
            "progress": 1.0,
            "phase": "training",
            "stage": "训练完成",
            "message": "训练任务已完成，正在启动自动GGUF导出...",
            "final_loss": final_state.get("loss"),
            "final_eval_loss": final_state.get("eval_loss"),
        })

        # 从 task config 读取 base_model
        db_conn = _get_db_conn()
        base_model = ""
        try:
            from src.adapters.repositories.task_repo import TaskRepository

            if db_conn:
                repo = TaskRepository(db_conn)
                task = repo.find_by_id(task_id)
                if task:
                    cfg = json.loads(task.config)
                    base_model = cfg.get("base_model", "")
        except Exception:
            pass

        # 执行导出阶段
        export_status = _run_export_phase(job_id, task_id, output_dir, base_model, db_conn)

        if db_conn:
            try:
                db_conn.dispose()
            except Exception:
                pass

        _logger.info("[Monitor] 训练+导出结束: job_id=%s, export_status=%s", job_id, export_status)
        return {"job_id": job_id, "task_id": task_id, "status": export_status}
    else:
        # 训练失败
        final_msg = {
            "status": "failed",
            "progress": 0.0,
            "stage": "训练异常",
            "message": "训练进程已退出但未找到完整训练记录",
        }
        _publish(job_id, final_msg)
        _update_task_status(task_id, "failed")

        _logger.info("[Monitor] 训练监控结束: job_id=%s, final_status=failed", job_id)
        return {"job_id": job_id, "task_id": task_id, "status": "failed"}