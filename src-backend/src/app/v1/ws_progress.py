# ruff: noqa: RUF002
"""WebSocket 进度路由 —— /ws/progress?job_id=xxx"""

from fastapi import APIRouter, Query, WebSocket
from src.services.progress_manager import get_progress_manager

router = APIRouter()


@router.websocket("/ws/progress")
async def websocket_progress(
    websocket: WebSocket,
    job_id: str = Query(..., description="GraphGen job_id"),
):
    """连接 Redis Pub/Sub，实时推送任务进度消息到前端。

    消息格式::

        {
            "stage": "环境就绪",
            "progress": 0.05,
            "message": "GraphGen: running",
            "status": "running"
        }
    """
    manager = get_progress_manager()
    await manager.subscribe(websocket, job_id)
