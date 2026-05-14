from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

_logger = logging.getLogger(__name__)


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


class LlamaFactoryFinetunedModelsResponse(BaseModel):
    success: bool = False
    fine_tuned: list[str] = Field(default_factory=list)
    online: list[str] = Field(default_factory=list)
    error: str | None = None


class LlamaFactoryTrainingRequest(BaseModel):
    task_name: str = Field(min_length=2, max_length=60)
    base_model: str
    finetune_method: str = "lora"
    dataset_id: int
    params: dict[str, Any] = Field(default_factory=dict)


class LlamaFactoryTrainingResponse(BaseModel):
    success: bool = False
    task_id: int | None = None
    job_id: str | None = None
    error: str | None = None


class LlamaFactoryExportRequest(BaseModel):
    """导出任务请求。"""

    task_name: str = Field(min_length=2, max_length=60)
    base_model: str
    adapter_path: str = ""
    params: dict[str, Any] = Field(default_factory=dict)
    # 可选字段（来自 params）：
    #   export_format: str  (gguf / pytorch / gptq / awq)
    #   quantization_method: str  (q4_k_m / q5_k_m / q8_0 / f16 / f32)
    #   export_path: str  (指定输出路径)


class LlamaFactoryExportResponse(BaseModel):
    """导出任务响应。"""

    success: bool = False
    task_id: int | None = None
    job_id: str | None = None
    export_path: str | None = None
    error: str | None = None


class LlamaFactoryCheckpointsResponse(BaseModel):
    """训练任务检查点列表响应。"""

    success: bool = False
    checkpoints: list[dict[str, Any]] = Field(default_factory=list)
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
        if self._llama.inference is None:
            return LlamaFactoryModelsResponse(error="LlamaFactory 推理服务未启动，请先启动 LlamaFactory API 服务")
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
        if self._llama.inference is None:
            return LlamaFactoryChatResponse(error="LlamaFactory 推理服务未启动，请先启动 LlamaFactory API 服务")
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

    async def stream_chat(self, request: LlamaFactoryChatRequest):
        """流式对话，返回 async generator 用于 SSE StreamingResponse。"""
        if self._llama.inference is None:
            return

        from src.adapters.llamafactory_async_inference_client import (
            LlamaFactoryAsyncInferenceClient,
        )
        from src.services.interfaces.http_client import HTTPClientConfig

        cfg = HTTPClientConfig(
            name="LlamaFactory Async Inference",
            url=self._llama.inference.config.url,
            retries=self._llama.inference.config.retries,
            timeout=self._llama.inference.config.timeout,
        )
        async_client = LlamaFactoryAsyncInferenceClient(cfg)
        async with async_client:
            async for chunk in async_client.stream_chat(
                model=request.model,
                messages=request.messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            ):
                yield chunk

    def list_finetuned_models(self) -> LlamaFactoryFinetunedModelsResponse:
        """返回微调产物列表与在线服务列表。"""
        all_models_resp = self.list_models()
        if not all_models_resp.success:
            return LlamaFactoryFinetunedModelsResponse(error=all_models_resp.error)

        fine_tuned_patterns = ("lora", "adapter", "merged", "finetuned", "ft-", "sft")
        fine_tuned: list[str] = []
        online: list[str] = []

        for model_id in all_models_resp.models:
            lower = model_id.lower()
            if any(p in lower for p in fine_tuned_patterns):
                fine_tuned.append(model_id)
                online.append(model_id)

        return LlamaFactoryFinetunedModelsResponse(
            success=True,
            fine_tuned=fine_tuned,
            online=online,
        )

    def list_checkpoints(self, training_task_id: int) -> LlamaFactoryCheckpointsResponse:
        """列出训练任务的所有检查点（从 output_dir 扫描 checkpoint-* 目录）。"""
        t = self._task_repo.find_by_id(training_task_id)
        if t is None:
            return LlamaFactoryCheckpointsResponse(error=f"Task not found: {training_task_id}")

        try:
            cfg = json.loads(t.config)
            output_dir = cfg.get("output_dir", "")
        except Exception:
            return LlamaFactoryCheckpointsResponse(error="Invalid task config")

        if not output_dir or not os.path.exists(output_dir):
            return LlamaFactoryCheckpointsResponse(success=True, checkpoints=[])

        checkpoints: list[dict[str, Any]] = []
        try:
            for entry in os.scandir(output_dir):
                if entry.is_dir() and entry.name.startswith("checkpoint-"):
                    adapter_file = Path(output_dir) / entry.name / "adapter_model.safetensors"
                    checkpoints.append({
                        "name": entry.name,
                        "path": entry.path,
                        "step": self._parse_step(entry.name),
                        "has_adapter": adapter_file.exists(),
                    })
        except Exception as exc:
            _logger.warning("[Export] 扫描检查点目录失败: %s", exc)

        checkpoints.sort(key=lambda x: x["step"] if x["step"] else 0)
        return LlamaFactoryCheckpointsResponse(success=True, checkpoints=checkpoints)

    @staticmethod
    def _parse_step(name: str) -> int:
        try:
            return int(name.split("-")[-1])
        except (ValueError, IndexError):
            return 0

    def submit_export(self, request: LlamaFactoryExportRequest, owner_id: int) -> LlamaFactoryExportResponse:
        """提交导出任务：查找训练产出 → 创建导出任务记录 → 启动子进程。"""
        if self._llama.export is None:
            return LlamaFactoryExportResponse(error="Export client not initialized")

        from src.adapters.llamafactory_export_client import ExportConfig

        params = request.params
        export_config = ExportConfig(
            base_model=request.base_model,
            adapter_path=request.adapter_path,
            export_format=params.get("export_format", "gguf"),
            quantization_method=params.get("quantization_method", "q4_k_m"),
            export_path=params.get("export_path", ""),
        )

        result = self._llama.export.submit_export(export_config)
        if not result.success:
            return LlamaFactoryExportResponse(error=result.error)

        from src.core.task_record import TaskRecord

        task = TaskRecord(
            owner_id=owner_id,
            task_name=request.task_name,
            task_type="export",
            status="running",
            config=TaskRecord.config_to_json({
                "job_id": result.job_id,
                "base_model": request.base_model,
                "adapter_path": request.adapter_path,
                "export_format": params.get("export_format", "gguf"),
                "quantization_method": params.get("quantization_method", "q4_k_m"),
                "export_path": result.export_path,
            }),
        )
        error = self._task_repo.insert(task)
        if error:
            _logger.error("[Export] 任务记录创建失败: %s", error)
            return LlamaFactoryExportResponse(error=f"任务记录创建失败: {error}")

        if task.id is None:
            _logger.error("[Export] 任务记录插入后未获取到 ID")
            return LlamaFactoryExportResponse(error="任务记录创建异常：未获取到任务ID")

        if self._celery is not None:
            try:
                self._celery.send_task(
                    "export.monitor",
                    kwargs={"job_id": result.job_id, "task_id": task.id},
                )
                _logger.info("[Export] 监控任务已下发: job_id=%s, task_id=%s", result.job_id, task.id)
            except Exception as exc:
                _logger.warning("[Export] 监控任务下发失败: %s — 导出进度将无法实时推送", exc)
        else:
            _logger.warning("[Export] Celery 未就绪，监控任务不会下发 — job_id=%s", result.job_id)

        _logger.info("[Export] 导出任务已提交: task_id=%s, job_id=%s", task.id, result.job_id)

        return LlamaFactoryExportResponse(
            success=True,
            task_id=task.id,
            job_id=result.job_id,
            export_path=result.export_path,
        )

    def submit_training(self, request: LlamaFactoryTrainingRequest, owner_id: int) -> LlamaFactoryTrainingResponse:
        """提交微调训练任务：验证数据集 → 同步到 LlamaFactory → 创建任务记录 → 启动子进程。"""
        dataset = self._dataset_repo.find_by_id(request.dataset_id)
        if dataset is None or dataset.owner_id != owner_id:
            return LlamaFactoryTrainingResponse(error=f"Dataset not found: {request.dataset_id}")

        if self._llama.training is None:
            return LlamaFactoryTrainingResponse(error="Training client not initialized")

        try:
            sync_result = self._llama.datasets.sync_dataset(
                dataset=dataset, dataset_name=dataset.name
            )
            dataset_name = sync_result["dataset_name"]
        except Exception as exc:
            _logger.error("[Training] 数据集同步失败: %s", exc)
            return LlamaFactoryTrainingResponse(error=f"数据集同步失败: {exc}")

        from src.adapters.llamafactory_training_client import TrainingConfig

        params = request.params
        training_config = TrainingConfig(
            base_model=request.base_model,
            finetune_method=request.finetune_method,
            dataset_name=dataset_name,
            epochs=params.get("epochs", 3),
            batch_size=params.get("batch_size", 2),
            learning_rate=params.get("learning_rate", 5e-5),
            max_seq_length=params.get("max_seq_length", 1024),
            lora_rank=params.get("lora_rank", 8),
            lora_alpha=params.get("lora_alpha", 16),
            lora_dropout=params.get("lora_dropout", 0.05),
            lora_target=params.get("lora_target", "all"),
            gradient_accumulation_steps=params.get("gradient_accumulation_steps", 4),
            weight_decay=params.get("weight_decay", 0.01),
            warmup_ratio=params.get("warmup_ratio", 0.1),
            optimizer=params.get("optimizer", "adamw_torch"),
            scheduler=params.get("scheduler", "cosine"),
            fp16=params.get("fp16", False),
            bf16=params.get("bf16", True),
            gradient_checkpointing=params.get("gradient_checkpointing", True),
        )

        result = self._llama.training.submit_training(training_config)
        if not result.success:
            return LlamaFactoryTrainingResponse(error=result.error)

        from src.core.task_record import TaskRecord

        task = TaskRecord(
            owner_id=owner_id,
            task_name=request.task_name,
            task_type="training",
            status="running",
            config=TaskRecord.config_to_json({
                "job_id": result.job_id,
                "dataset_id": request.dataset_id,
                "base_model": request.base_model,
                "finetune_method": request.finetune_method,
                "output_dir": result.output_dir,
                "params": request.params,
            }),
        )
        error = self._task_repo.insert(task)
        if error:
            _logger.error("[Training] 任务记录创建失败: %s", error)
            return LlamaFactoryTrainingResponse(error=f"任务记录创建失败: {error}")

        if task.id is None:
            _logger.error("[Training] 任务记录插入后未获取到 ID")
            return LlamaFactoryTrainingResponse(error="任务记录创建异常：未获取到任务ID")

        if self._celery is not None:
            try:
                self._celery.send_task(
                    "training.monitor",
                    kwargs={"job_id": result.job_id, "task_id": task.id},
                )
                _logger.info("[Training] 监控任务已下发: job_id=%s, task_id=%s", result.job_id, task.id)
            except Exception as exc:
                _logger.error("[Training] 监控任务下发失败: %s — 训练进度将无法实时推送", exc)
                # 不影响训练主流程，仅监控不可用
        else:
            _logger.warning("[Training] Celery 未就绪，监控任务不会下发 — job_id=%s", result.job_id)

        _logger.info("[Training] 训练任务已提交: task_id=%s, job_id=%s", task.id, result.job_id)

        return LlamaFactoryTrainingResponse(
            success=True,
            task_id=task.id,
            job_id=result.job_id,
        )
