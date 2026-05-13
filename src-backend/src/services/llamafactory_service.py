from typing import Any

from pydantic import BaseModel, Field


class LlamaFactoryDatasetSyncRequest(BaseModel):
    dataset_id: int
    dataset_name: str | None = Field(default=None, min_length=1, max_length=120)


class LlamaFactoryDatasetSyncResponse(BaseModel):
    success: bool = False
    dataset_id: int | None = None
    dataset_name: str | None = None
    file_name: str | None = None
    target_path: str | None = None
    error: str | None = None


class LlamaFactoryChatRequest(BaseModel):
    model: str
    messages: list[dict[str, Any]]
    temperature: float | None = Field(default=None, ge=0.0)
    max_tokens: int | None = Field(default=None, ge=1)


class LlamaFactoryModelsResponse(BaseModel):
    success: bool = False
    models: list[str] = Field(default_factory=list)
    raw_response: dict[str, Any] | None = None
    error: str | None = None


class LlamaFactoryChatResponse(BaseModel):
    success: bool = False
    content: str | None = None
    raw_response: dict[str, Any] | None = None
    error: str | None = None


class LlamaFactoryService:
    def __init__(self, *, dataset_repo, task_repo, file_repo, llama_client, celery_client=None) -> None:
        self._dataset_repo = dataset_repo
        self._task_repo = task_repo
        self._file_repo = file_repo
        self._llama = llama_client
        self._celery = celery_client

    def sync_dataset(self, request: LlamaFactoryDatasetSyncRequest, owner_id: int) -> LlamaFactoryDatasetSyncResponse:
        dataset = self._dataset_repo.find_by_id(request.dataset_id)
        if dataset is None or dataset.owner_id != owner_id:
            return LlamaFactoryDatasetSyncResponse(error=f"Dataset not found: {request.dataset_id}")

        result = self._llama.datasets.sync_dataset(dataset=dataset, dataset_name=request.dataset_name)
        return LlamaFactoryDatasetSyncResponse(
            success=True,
            dataset_id=request.dataset_id,
            dataset_name=result["dataset_name"],
            file_name=result["file_name"],
            target_path=result["target_path"],
        )

    def list_models(self) -> LlamaFactoryModelsResponse:
        try:
            response = self._llama.inference.list_models()
            data = response.json()
        except Exception as exc:
            return LlamaFactoryModelsResponse(error=str(exc))

        items = data.get("data")
        if not isinstance(items, list):
            return LlamaFactoryModelsResponse(error="Invalid LlamaFactory models response: data")

        models: list[str] = []
        for item in items:
            if isinstance(item, dict):
                model_id = item.get("id")
                if isinstance(model_id, str) and model_id:
                    models.append(model_id)

        return LlamaFactoryModelsResponse(success=True, models=models, raw_response=data)

    def chat(self, request: LlamaFactoryChatRequest) -> LlamaFactoryChatResponse:
        try:
            response = self._llama.inference.chat(
                model=request.model,
                messages=request.messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )
            data = response.json()
        except Exception as exc:
            return LlamaFactoryChatResponse(error=str(exc))

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            return LlamaFactoryChatResponse(error=f"Invalid LlamaFactory chat response: {exc}")

        return LlamaFactoryChatResponse(success=True, content=content, raw_response=data)
