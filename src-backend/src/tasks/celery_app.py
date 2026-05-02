"""Celery 实例 —— 仅负责 broker/backend 连接和任务注册。"""
from celery import Celery

from src.core.config import config

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
    worker_pool="solo",
    task_track_started=True,
)

# 注册任务模块
import src.tasks.dataset_tasks  # noqa: E402, F401
