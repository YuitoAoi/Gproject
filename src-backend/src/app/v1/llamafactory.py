from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from src.app.dependencies import get_current_user, get_services
from src.services import (
    LlamaFactoryChatRequest,
    LlamaFactoryChatResponse,
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
