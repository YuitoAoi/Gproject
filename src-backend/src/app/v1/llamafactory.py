from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from src.app.dependencies import get_current_user, get_services
from src.services import (
    LlamaFactoryChatRequest,
    LlamaFactoryChatResponse,
    LlamaFactoryCheckpointsResponse,
    LlamaFactoryExportRequest,
    LlamaFactoryExportResponse,
    LlamaFactoryFinetunedModelsResponse,
    LlamaFactoryModelsResponse,
    LlamaFactoryTrainingRequest,
    LlamaFactoryTrainingResponse,
    ServiceFactory,
)
from src.services.jwt_service import TokenPayload

router = APIRouter(prefix="/llamafactory", tags=["llamafactory"])


@router.get("/models", response_model=LlamaFactoryModelsResponse)
def list_models(
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    _ = current_user
    result = svc.llamafactory().list_models()
    if not result.success:
        return JSONResponse(content=result.model_dump(mode="json"), status_code=502)
    return result


@router.post("/chat", response_model=LlamaFactoryChatResponse)
def chat(
    request: LlamaFactoryChatRequest,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    _ = current_user
    result = svc.llamafactory().chat(request)
    if not result.success:
        return JSONResponse(content=result.model_dump(mode="json"), status_code=502)
    return result


@router.post("/chat/stream")
async def chat_stream(
    request: LlamaFactoryChatRequest,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    """SSE 流式对话接口。"""
    _ = current_user
    generator = svc.llamafactory().stream_chat(request)
    if generator is None:
        return JSONResponse(
            content={"error": "LlamaFactory 推理服务未启动，请先启动 LlamaFactory API 服务"},
            status_code=503,
        )
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/finetuned-models", response_model=LlamaFactoryFinetunedModelsResponse)
def list_finetuned_models(
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    """返回微调产物列表与在线服务列表。"""
    _ = current_user
    return svc.llamafactory().list_finetuned_models()


@router.post("/inference/start")
def start_inference(
    model_id: str,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    """启动指定模型的在线推理服务（通过 LlamaFactory API 预加载模型）。"""
    _ = current_user
    result = svc.llamafactory().chat(
        LlamaFactoryChatRequest(model=model_id, messages=[{"role": "user", "content": "ping"}])
    )
    return {"success": result.success, "error": result.error}


@router.post("/train", response_model=LlamaFactoryTrainingResponse)
def submit_training(
    request: LlamaFactoryTrainingRequest,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    """提交微调训练任务。

    流程：验证数据集 → 同步到 LlamaFactory → 创建 TaskRecord → 启动子进程 → 返回 task_id。
    """
    owner_id = int(current_user.user_id)
    result = svc.llamafactory().submit_training(request, owner_id)
    if not result.success:
        return JSONResponse(content=result.model_dump(mode="json"), status_code=400)
    return result


@router.post("/export", response_model=LlamaFactoryExportResponse)
def submit_export(
    request: LlamaFactoryExportRequest,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    """提交模型导出任务。"""
    owner_id = int(current_user.user_id)
    result = svc.llamafactory().submit_export(request, owner_id)
    if not result.success:
        return JSONResponse(content=result.model_dump(mode="json"), status_code=400)
    return result


@router.get("/checkpoints/{training_task_id}", response_model=LlamaFactoryCheckpointsResponse)
def list_checkpoints(
    training_task_id: int,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    """列出指定训练任务的所有检查点。"""
    _ = current_user
    return svc.llamafactory().list_checkpoints(training_task_id)


@router.get("/export/{task_id}/log")
def get_export_log(
    task_id: int,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    """读取导出任务的日志文件。"""
    t = svc.task_repo.find_by_id(task_id)
    if t is None or t.owner_id != int(current_user.user_id):
        raise HTTPException(status_code=404, detail="任务未找到")

    import json as _json
    job_id = None
    try:
        cfg = _json.loads(t.config)
        job_id = cfg.get("job_id")
    except Exception:
        raise HTTPException(status_code=400, detail="任务配置无效")

    from src.core.config import config
    import os
    log_file = os.path.join(config.LLAMAFACTORY_JOB_DIR, job_id, "export.log")
    if not os.path.exists(log_file):
        return {"lines": [], "error": "日志文件尚未生成"}

    try:
        with open(log_file, encoding="utf-8") as f:
            lines = [line.rstrip("\n") for line in f.readlines()]
        return {"lines": lines}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/export/{task_id}/terminate")
def terminate_export(
    task_id: int,
    svc: ServiceFactory = Depends(get_services),
    current_user: TokenPayload = Depends(get_current_user),
):
    """强制终止导出任务。"""
    t = svc.task_repo.find_by_id(task_id)
    if t is None or t.owner_id != int(current_user.user_id):
        raise HTTPException(status_code=404, detail="任务未找到")

    if t.task_type != "export":
        raise HTTPException(status_code=400, detail="仅支持终止导出任务")

    import json as _json
    job_id = None
    try:
        cfg = _json.loads(t.config)
        job_id = cfg.get("job_id")
    except Exception:
        raise HTTPException(status_code=400, detail="任务配置无效")

    import os
    import signal
    from pathlib import Path
    from src.core.config import config

    job_dir = Path(config.LLAMAFACTORY_JOB_DIR) / job_id
    pid_path = job_dir / "pid"

    terminated = False
    if pid_path.exists():
        try:
            pid = int(pid_path.read_text(encoding="utf-8").strip())
            if os.name == "nt":
                import ctypes
                kernel32 = ctypes.windll.kernel32
                handle = kernel32.OpenProcess(1, False, pid)
                if handle:
                    kernel32.TerminateProcess(handle, 0)
                    kernel32.CloseHandle(handle)
                    terminated = True
            else:
                os.kill(pid, signal.SIGTERM)
                terminated = True
        except Exception:
            pass

    svc.task_repo.update_status(task_id, "cancelled")
    return {"success": True, "terminated": terminated, "message": "导出任务已终止" if terminated else "进程未找到，标记为已终止"}
