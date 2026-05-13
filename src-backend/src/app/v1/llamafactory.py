from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from src.app.dependencies import get_current_user, get_services
from src.services import (
    LlamaFactoryChatRequest,
    LlamaFactoryChatResponse,
    LlamaFactoryModelsResponse,
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
