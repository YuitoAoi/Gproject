"""任务路由 —— GET /tasks, POST /tasks, GET /tasks/{id}, PATCH /tasks/{id}, DELETE /tasks/{id}, POST /tasks/{id}/dispatch"""

import json
import logging
import os
import shutil
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from src.app.dependencies import get_current_user, get_services
from src.core.task_record import TASK_STATUS, TASK_TYPE
from src.services import ServiceFactory
from src.services.jwt_service import TokenPayload

_logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskItem(BaseModel):
    id: int
    task_name: str
    task_type: TASK_TYPE
    status: TASK_STATUS
    progress: float
    phase: str
    config: str
    created_at: str
    updated_at: str


class TaskCreateRequest(BaseModel):
    task_name: str
    task_type: TASK_TYPE = "cleaning"
    config: str = "{}"


class TaskListResponse(BaseModel):
    items: list[TaskItem]
    total: int
    page: int = 1
    page_size: int = 20
    error: str | None = None


class TaskDetailResponse(BaseModel):
    task: TaskItem | None = None
    error: str | None = None


class TaskUpdateRequest(BaseModel):
    status: TASK_STATUS | None = None
    progress: float | None = Field(None, ge=0.0, le=1.0)
    phase: str | None = None


class TaskUpdateResponse(BaseModel):
    task: TaskItem | None = None
    error: str | None = None


def _task_to_item(t) -> TaskItem:
    return TaskItem(
        id=t.id,
        task_name=t.task_name,
        task_type=t.task_type,
        status=t.status,
        progress=t.progress,
        phase=t.phase,
        config=t.config,
        created_at=t.created_at.isoformat(),
        updated_at=t.updated_at.isoformat(),
    )


@router.get("", response_model=TaskListResponse)
def list_tasks(
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    owner_id = int(current_user.user_id)
    try:
        items, total = svc.task_repo.find_by_owner_paged(owner_id, page, page_size, status)
        return TaskListResponse(items=[_task_to_item(t) for t in items], total=total, page=page, page_size=page_size)
    except Exception as e:
        return TaskListResponse(items=[], total=0, error=str(e))


@router.post("", response_model=TaskDetailResponse, status_code=201)
def create_task(
    request: TaskCreateRequest,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    owner_id = int(current_user.user_id)
    from src.core.task_record import TaskRecord

    task = TaskRecord(
        owner_id=owner_id,
        task_name=request.task_name,
        task_type=request.task_type,
        config=request.config,
    )
    _logger.info(f"[create_task] Creating task: name={request.task_name}, type={request.task_type}, owner={owner_id}")
    error = svc.task_repo.insert(task)
    if error:
        _logger.error(f"[create_task] Insert failed: {error}")
        raise HTTPException(status_code=500, detail=f"Failed to create task: {error}")
    if task.id is None:
        _logger.error("[create_task] task.id is None after insert")
        raise HTTPException(status_code=500, detail="Failed to retrieve task ID after insert")
    _logger.info(f"[create_task] Task created successfully: id={task.id}")
    return TaskDetailResponse(task=_task_to_item(task))


@router.patch("/{task_id}", response_model=TaskUpdateResponse)
def update_task(
    task_id: int,
    request: TaskUpdateRequest,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    owner_id = int(current_user.user_id)
    t = svc.task_repo.find_by_id(task_id)
    if t is None or t.owner_id != owner_id:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

    if request.status is not None:
        t.status = request.status
    if request.progress is not None:
        t.progress = request.progress
    if request.phase is not None:
        t.phase = request.phase
    t.updated_at = datetime.now()

    error = svc.task_repo.update(task_id, t)
    if error:
        return TaskUpdateResponse(error=str(error))
    return TaskUpdateResponse(task=_task_to_item(t))


@router.post("/{task_id}/dispatch")
def dispatch_task(
    task_id: int,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    from src.adapters.celery_client import celery_client

    t = svc.task_repo.find_by_id(task_id)
    if t is None or t.owner_id != int(current_user.user_id):
        raise HTTPException(status_code=404, detail="Task not found")

    try:
        config = json.loads(t.config)
        job_id = config.get("job_id")
        dataset_id = config.get("dataset_id")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid task config") from e

    if not job_id or not dataset_id:
        raise HTTPException(status_code=400, detail="Task config missing job_id or dataset_id")

    if t.task_type == "training":
        celery_client.send_task("training.monitor", kwargs={"job_id": job_id, "task_id": task_id})
    elif t.task_type == "cleaning":
        celery_client.send_task("dataset.monitor_graphgen", kwargs={"job_id": job_id, "dataset_id": dataset_id})
    else:
        raise HTTPException(status_code=400, detail=f"Task type {t.task_type} does not support dispatch")

    return {"success": True, "message": "Task dispatched"}


@router.get("/{task_id}", response_model=TaskDetailResponse)
def get_task(
    task_id: int,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    owner_id = int(current_user.user_id)
    t = svc.task_repo.find_by_id(task_id)
    if t is None or t.owner_id != owner_id:
        return TaskDetailResponse(error=f"Task not found: {task_id}")
    return TaskDetailResponse(task=_task_to_item(t))


LOG_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "data",
    "logs",
    "dataset_logs",
)
LOG_DIR = os.path.normpath(LOG_DIR)

# 训练日志目录：与 LlamaFactory 任务目录复用，resolve 为绝对路径
from src.core.config import config as _cfg
from pathlib import Path

TRAINING_JOB_DIR = str((Path(__file__).parent / ".." / ".." / ".." / _cfg.LLAMAFACTORY_JOB_DIR).resolve())


@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    owner_id = int(current_user.user_id)
    t = svc.task_repo.find_by_id(task_id)
    if t is None or t.owner_id != owner_id:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

    job_id = None
    try:
        config = json.loads(t.config)
        job_id = config.get("job_id")
    except Exception:
        pass

    if job_id:
        svc.dataset_log_repo.remove_by_job_id(job_id)
        dataset_log_file = os.path.join(LOG_DIR, f"{job_id}.log")
        if os.path.exists(dataset_log_file):
            import contextlib

            with contextlib.suppress(Exception):
                os.remove(dataset_log_file)

        # 清理训练任务目录（含 train.log、config.json、pid、output/）
        training_job_dir = os.path.join(TRAINING_JOB_DIR, job_id)
        if os.path.isdir(training_job_dir):
            with contextlib.suppress(Exception):
                shutil.rmtree(training_job_dir)

    svc.task_repo.remove(task_id)
    return {"success": True}


class TrainingTerminateResponse(BaseModel):
    success: bool = False
    message: str = ""


@router.post("/{task_id}/terminate", response_model=TrainingTerminateResponse)
def terminate_training_task(
    task_id: int,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    """强制终止训练任务：kill 子进程并更新状态。"""
    owner_id = int(current_user.user_id)
    t = svc.task_repo.find_by_id(task_id)
    if t is None or t.owner_id != owner_id:
        raise HTTPException(status_code=404, detail="Task not found")

    if t.task_type != "training":
        raise HTTPException(status_code=400, detail="Only training tasks can be terminated via this endpoint")

    try:
        config = json.loads(t.config)
        job_id = config.get("job_id")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid task config") from e

    if not job_id:
        raise HTTPException(status_code=400, detail="Task config missing job_id")

    # 终止子进程
    terminated = False
    try:
        from src.core.task.training_monitor_task import JOB_DIR, _terminate_process, _cleanup_training_logs

        terminated = _terminate_process(job_id)
        _cleanup_training_logs(job_id)
    except Exception as exc:
        _logger.warning("[terminate_training] 无法终止进程 %s: %s", job_id, exc)

    # 更新任务状态
    svc.task_repo.update_status(task_id, "cancelled")

    _logger.info("[terminate_training] task_id=%s, job_id=%s, terminated=%s", task_id, job_id, terminated)
    return TrainingTerminateResponse(
        success=True,
        message="训练任务已终止" if terminated else "进程已标记终止（可能已自行退出）",
    )


class CleaningSummaryResponse(BaseModel):
    raw_count: int = 0
    final_count: int = 0
    status: str = "pending"
    current_stage: str = ""
    error: str | None = None


class TrainingLogResponse(BaseModel):
    lines: list[str] = []
    error: str | None = None


@router.get("/{task_id}/training-log", response_model=TrainingLogResponse)
def get_training_log(
    task_id: int,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    """读取训练任务的日志文件（train.log）。"""
    owner_id = int(current_user.user_id)
    t = svc.task_repo.find_by_id(task_id)
    if t is None or t.owner_id != owner_id:
        return TrainingLogResponse(error="任务未找到")

    if t.task_type != "training":
        return TrainingLogResponse(error="仅训练任务有日志")

    job_id = None
    try:
        config = json.loads(t.config)
        job_id = config.get("job_id")
    except Exception:
        return TrainingLogResponse(error="任务配置无效")

    if not job_id:
        return TrainingLogResponse(error="缺少 job_id")

    # 训练日志位于 job_dir/train.log
    log_file = os.path.join(TRAINING_JOB_DIR, job_id, "train.log")
    if not log_file.exists():
        return TrainingLogResponse(error="日志文件尚未生成")

    try:
        with open(log_file, encoding="utf-8") as f:
            lines = [line.rstrip("\n") for line in f.readlines()]
        return TrainingLogResponse(lines=lines)
    except Exception as exc:
        return TrainingLogResponse(error=str(exc))


@router.get("/{task_id}/cleaning-summary", response_model=CleaningSummaryResponse)
def get_cleaning_summary(
    task_id: int,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    owner_id = int(current_user.user_id)
    t = svc.task_repo.find_by_id(task_id)
    if t is None or t.owner_id != owner_id:
        return CleaningSummaryResponse(error=f"Task not found: {task_id}")

    try:
        config = json.loads(t.config)
    except Exception:
        config = {}

    raw_count = config.get("raw_count", 0)
    final_count = config.get("final_count", 0)

    return CleaningSummaryResponse(
        raw_count=raw_count,
        final_count=final_count,
        status=t.status.value if hasattr(t.status, "value") else str(t.status),
        current_stage=t.phase or "read",
    )
