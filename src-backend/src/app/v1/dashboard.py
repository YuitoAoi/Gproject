# ruff: noqa: RUF002, RUF003
"""仪表盘路由 —— GET /dashboard 聚合所有仪表盘数据。"""

from __future__ import annotations

import logging
import shutil

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.app.dependencies import get_current_user, get_services
from src.services import ServiceFactory
from src.services.jwt_service import TokenPayload

_logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


# ── 响应模型 ─────────────────────────────────────────────


class ServiceHealthItem(BaseModel):
    title: str
    status: str
    time: str
    class_: str
    icon: str


class StorageInfo(BaseModel):
    total_gb: float
    used_gb: float
    free_gb: float
    percentage: float


class TaskBriefingItem(BaseModel):
    taskName: str
    phase: str
    progress: float


class AuditTrailItem(BaseModel):
    time: str
    status: str
    content: str


class DailyCountItem(BaseModel):
    date: str
    count: int


class DashboardResponse(BaseModel):
    active_task_count: int = 0
    dataset_count: int = 0
    finetuned_model_count: int = 0
    compute_task_count: int = 0
    service_health: list[ServiceHealthItem] = []
    storage: StorageInfo | None = None
    daily_done: list[DailyCountItem] = []
    task_briefing: list[TaskBriefingItem] = []
    audit_trail: list[AuditTrailItem] = []
    error: str | None = None


# ── 健康检测辅助 ──────────────────────────────────────────


def _check_redis() -> ServiceHealthItem:
    from src.core.config import config

    try:
        import redis

        r = redis.Redis.from_url(config.REDIS_URL)
        r.ping()
        r.close()
        return ServiceHealthItem(
            title="Redis",
            status="正常",
            time="运行中",
            class_="bg-green-100 text-green-600",
            icon="ri:database-2-line",
        )
    except Exception:
        return ServiceHealthItem(
            title="Redis",
            status="异常",
            time="已停止",
            class_="bg-red-100 text-red-600",
            icon="ri:database-2-line",
        )


def _check_celery() -> ServiceHealthItem:
    try:
        from src.adapters.celery_client import celery_client

        result = celery_client.control.ping(timeout=3)
        if result:
            return ServiceHealthItem(
                title="Celery",
                status="正常",
                time="运行中",
                class_="bg-green-100 text-green-600",
                icon="ri:timer-flash-line",
            )
    except Exception:
        pass
    return ServiceHealthItem(
        title="Celery",
        status="异常",
        time="已停止",
        class_="bg-red-100 text-red-600",
        icon="ri:timer-flash-line",
    )


def _build_service_health() -> list[ServiceHealthItem]:
    """构建服务健康状态列表。"""
    items = [
        _check_redis(),
        _check_celery(),
        # WebSocket 随 FastAPI 服务运行，始终可用
        ServiceHealthItem(
            title="WebSocket",
            status="正常",
            time="运行中",
            class_="bg-green-100 text-green-600",
            icon="ri:wifi-line",
        ),
        ServiceHealthItem(
            title="GPU Driver",
            status="未监控",
            time="—",
            class_="bg-gray-100 text-gray-600",
            icon="ri:hard-drive-3-line",
        ),
    ]
    return items


def _build_storage_info() -> StorageInfo | None:
    """检测数据目录所在磁盘使用情况。"""
    import os

    from src.core.config import config

    data_dir = os.path.abspath(config.DATASETS_DIR)
    if not os.path.exists(data_dir):
        # 尝试使用父目录
        data_dir = os.path.dirname(data_dir)
    if not os.path.exists(data_dir):
        return None

    try:
        usage = shutil.disk_usage(data_dir)
        total_gb = round(usage.total / (1024**3), 1)
        used_gb = round(usage.used / (1024**3), 1)
        free_gb = round(usage.free / (1024**3), 1)
        percentage = round(usage.used / usage.total * 100, 1) if usage.total > 0 else 0
        return StorageInfo(total_gb=total_gb, used_gb=used_gb, free_gb=free_gb, percentage=percentage)
    except Exception:
        _logger.exception("Failed to get disk usage")
        return None


def _build_audit_trail(tasks) -> list[AuditTrailItem]:
    """将任务列表转换为审计追踪格式。"""
    from datetime import datetime

    status_map = {
        "done": "success",
        "running": "primary",
        "failed": "danger",
        "cancelled": "warning",
        "pending": "primary",
    }
    phase_desc_map = {
        "training": "训练完成",
        "cleaning": "数据清洗完成",
        "inference": "推理完成",
        "export": "模型导出完成",
        "upload": "数据上传完成",
    }
    items: list[AuditTrailItem] = []
    now = datetime.now()
    for t in tasks[:10]:
        delta = now - t.updated_at
        if delta.days > 0:
            time_str = f"{delta.days} 天前"
        elif delta.seconds >= 3600:
            time_str = f"{delta.seconds // 3600} 小时前"
        elif delta.seconds >= 60:
            time_str = f"{delta.seconds // 60} 分钟前"
        else:
            time_str = "刚刚"

        if t.status == "done":
            action = phase_desc_map.get(t.task_type, "任务完成")
            content = f"{t.task_name} {action}"
        elif t.status == "failed":
            content = f"{t.task_name} 执行失败"
        elif t.status == "running":
            content = f"{t.task_name} 正在执行"
        else:
            content = f"{t.task_name} 状态更新"

        items.append(
            AuditTrailItem(
                time=time_str,
                status=status_map.get(t.status, "primary"),
                content=content,
            )
        )
    return items


# ── 路由 ──────────────────────────────────────────────────


@router.get("", response_model=DashboardResponse)
def get_dashboard(
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    """聚合仪表盘所有数据。每个数据源独立 try/except，单个失败不影响其余。"""
    owner_id = int(current_user.user_id)

    # 1. 活动任务数（运行中 + 排队中）
    active_task_count = 0
    try:
        active_task_count = svc.task_repo.count_by_status(owner_id, ["running", "pending"])
    except Exception:
        _logger.exception("Failed to get active task count")

    # 2. 数据集数量
    dataset_count = 0
    try:
        dataset_count = svc.dataset_repo.count_by_owner(owner_id)
    except Exception:
        _logger.exception("Failed to get dataset count")

    # 3. 已微调模型数量
    finetuned_model_count = 0
    try:
        result = svc.llamafactory().list_finetuned_models()
        if result.success:
            finetuned_model_count = len(result.fine_tuned)
    except Exception:
        _logger.exception("Failed to get finetuned model count")

    # 4. 已完成任务数（算力消耗代理指标）
    compute_task_count = 0
    try:
        compute_task_count = svc.task_repo.count_by_status(owner_id, ["done"])
    except Exception:
        _logger.exception("Failed to get compute task count")

    # 5. 服务健康状态
    service_health: list[ServiceHealthItem] = []
    try:
        service_health = _build_service_health()
    except Exception:
        _logger.exception("Failed to build service health")

    # 6. 存储水位
    storage: StorageInfo | None = None
    try:
        storage = _build_storage_info()
    except Exception:
        _logger.exception("Failed to build storage info")

    # 7. 最近 7 天每日完成任务数
    daily_done: list[DailyCountItem] = []
    try:
        raw = svc.task_repo.daily_done_counts(owner_id, 7)
        daily_done = [DailyCountItem(date=d, count=c) for d, c in raw]
    except Exception:
        _logger.exception("Failed to get daily done counts")

    # 8 & 9. 任务简报 + 审计追踪（共享一次查询）
    task_briefing: list[TaskBriefingItem] = []
    audit_trail: list[AuditTrailItem] = []
    try:
        recent = svc.task_repo.recent_tasks(owner_id, 10)
        task_briefing = [
            TaskBriefingItem(
                taskName=t.task_name,
                phase=t.phase or t.status,
                progress=round(t.progress * 100, 1),
            )
            for t in recent
        ]
        audit_trail = _build_audit_trail(recent)
    except Exception:
        _logger.exception("Failed to get task briefing / audit trail")

    return DashboardResponse(
        active_task_count=active_task_count,
        dataset_count=dataset_count,
        finetuned_model_count=finetuned_model_count,
        compute_task_count=compute_task_count,
        service_health=service_health,
        storage=storage,
        daily_done=daily_done,
        task_briefing=task_briefing,
        audit_trail=audit_trail,
    )
