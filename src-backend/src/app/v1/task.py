"""任务路由 —— GET /tasks, GET /tasks/{id}, DELETE /tasks/{id}"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.app.dependencies import get_current_user, get_services
from src.services import ServiceFactory
from src.services.jwt_service import TokenPayload

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskItem(BaseModel):
    id: int
    task_name: str
    task_type: str
    status: str
    progress: float
    phase: str
    config: str
    created_at: str
    updated_at: str


class TaskListResponse(BaseModel):
    items: List[TaskItem]
    total: int
    error: Optional[str] = None


class TaskDetailResponse(BaseModel):
    task: Optional[TaskItem] = None
    error: Optional[str] = None


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
    status: Optional[str] = None,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    owner_id = int(current_user.user_id)
    try:
        items = [
            _task_to_item(t)
            for t in svc.task_repo.find_by_owner(owner_id, status=status)
        ]
        return TaskListResponse(items=items, total=len(items))
    except Exception as e:
        return TaskListResponse(items=[], total=0, error=str(e))


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
    svc.task_repo.remove(task_id)
    return {"success": True}
