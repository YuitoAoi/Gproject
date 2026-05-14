"""共享 Celery 实例 —— backend 和 celery worker 共用。"""

from celery import Celery
from src.core.config import config

celery_client = Celery(
    "gproject",
    broker=config.CELERY_BROKER_URL,
    backend=config.CELERY_RESULT_BACKEND,
)

celery_client.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_soft_time_limit=25 * 60,
    task_time_limit=30 * 60,
    task_track_started=True,
    # 显式注册所有 Celery 任务模块，避免 Worker 启动时无法发现任务
    include=[
        "src.core.task.training_monitor_task",
    ],
)
