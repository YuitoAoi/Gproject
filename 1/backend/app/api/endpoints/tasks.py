from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from celery.result import AsyncResult
from app.tasks import add, multiply

router = APIRouter()

class TaskRequest(BaseModel):
    x: int
    y: int

class TaskResponse(BaseModel):
    task_id: str
    status: str
    result: int = None

@router.post("/tasks/add", response_model=TaskResponse)
async def create_add_task(request: TaskRequest):
    """创建加法任务"""
    task = add.delay(request.x, request.y)
    return TaskResponse(task_id=task.id, status="pending")

@router.post("/tasks/multiply", response_model=TaskResponse)
async def create_multiply_task(request: TaskRequest):
    """创建乘法任务"""
    task = multiply.delay(request.x, request.y)
    return TaskResponse(task_id=task.id, status="pending")

@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: str):
    """获取任务状态"""
    task_result = AsyncResult(task_id)
    
    response = TaskResponse(
        task_id=task_id,
        status=task_result.status
    )
    
    if task_result.ready():
        response.result = task_result.result
    
    return response