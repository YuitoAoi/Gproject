"""Celery Worker —— 独立构建，仅轮询 GraphGen + HTTP 回调 backend。"""
from celery import Celery

from config import config

celery_app = Celery(
    "gproject",
    broker=config.CELERY_BROKER_URL,
    backend=config.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_soft_time_limit=25 * 60,
    task_time_limit=30 * 60,
    task_track_started=True,
    # 注册训练监控任务，使 Worker 能发现 training.monitor
    include=[
        "tasks",
        "src.core.task.training_monitor_task",
    ],
)

import tasks  # noqa: E402, F401
