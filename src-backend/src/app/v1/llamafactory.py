from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from src.app.dependencies import get_current_user, get_services
from src.services import (
    LlamaFactoryChatRequest,
    LlamaFactoryChatResponse,
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
