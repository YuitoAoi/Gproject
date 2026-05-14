"""LlamaFactory 训练客户端 —— 通过 subprocess 调用 LlamaFactory CLI 启动微调任务。"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import uuid
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from src.core.config import config as proj_config

_logger = logging.getLogger(__name__)


class TrainingConfig(BaseModel):
    """训练任务配置参数。"""

    base_model: str
    finetune_method: str = "lora"
    dataset_name: str
    output_dir: str = ""

    epochs: int = 3
    batch_size: int = 2
    learning_rate: float = 5e-5
    max_seq_length: int = 1024

    lora_rank: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.05
    lora_target: str = "all"

    gradient_accumulation_steps: int = 4
    weight_decay: float = 0.01
    warmup_ratio: float = 0.1
    optimizer: str = "adamw_torch"
    scheduler: str = "cosine"

    fp16: bool = False
    bf16: bool = True
    gradient_checkpointing: bool = True


class TrainingResult(BaseModel):
    """训练任务提交结果。"""

    success: bool = False
    job_id: str = ""
    config_path: str = ""
    output_dir: str = ""
    error: str | None = None


class LlamaFactoryTrainingClient:
    """通过子进程调用 LlamaFactory CLI 执行模型微调。

    每次训练请求：
    1. 生成唯一 job_id
    2. 组装 YAML 配置文件写入 JOB_DIR
    3. 通过 subprocess.Popen 启动 ``llamafactory-cli train config.yaml``
    4. 返回 job_id 供上层追踪
    """

    def __init__(self) -> None:
        self._job_dir = Path(proj_config.LLAMAFACTORY_JOB_DIR)
        self._job_dir.mkdir(parents=True, exist_ok=True)
        self._data_dir = Path(proj_config.LLAMAFACTORY_DATA_DIR)
        self._train_cmd = proj_config.LLAMAFACTORY_TRAIN_COMMAND

    def submit_training(self, config: TrainingConfig) -> TrainingResult:
        """组装配置并提交训练子进程。"""
        job_id = f"train_{uuid.uuid4().hex[:12]}"
        job_dir = self._job_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        output_dir = config.output_dir or str(job_dir / "output")
        os.makedirs(output_dir, exist_ok=True)

        yaml_config = self._build_config(config, job_id, output_dir)
        config_path = job_dir / "train_config.json"

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(yaml_config, f, indent=2, ensure_ascii=False)

        _logger.info("[Training] 配置已写入: %s", config_path)

        log_path = job_dir / "train.log"

        try:
            cmd = [self._train_cmd, "train", str(config_path)]
            _logger.info("[Training] 启动命令: %s", " ".join(cmd))

            log_file = open(log_path, "w", encoding="utf-8")
            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    cwd=str(self._data_dir.parent),
                    env={**os.environ},
                )
            except Exception:
                log_file.close()
                raise

            pid_path = job_dir / "pid"
            pid_path.write_text(str(process.pid), encoding="utf-8")

            self._start_log_closer(process, log_file)

            return TrainingResult(
                success=True,
                job_id=job_id,
                config_path=str(config_path),
                output_dir=output_dir,
            )
        except FileNotFoundError:
            msg = f"LlamaFactory CLI 未找到: {self._train_cmd}"
            _logger.error("[Training] %s", msg)
            return TrainingResult(error=msg)
        except Exception as exc:
            _logger.error("[Training] 启动失败: %s", exc)
            return TrainingResult(error=str(exc))

    def _build_config(self, config: TrainingConfig, job_id: str, output_dir: str) -> dict[str, Any]:
        """组装 LlamaFactory 训练配置字典。"""
        cfg: dict[str, Any] = {
            "model_name_or_path": config.base_model,
            "stage": "sft",
            "do_train": True,
            "dataset": config.dataset_name,
            "template": self._detect_template(config.base_model),
            "finetuning_type": config.finetune_method,
            "output_dir": output_dir,
            "overwrite_output_dir": True,
            "per_device_train_batch_size": config.batch_size,
            "gradient_accumulation_steps": config.gradient_accumulation_steps,
            "learning_rate": config.learning_rate,
            "num_train_epochs": config.epochs,
            "cutoff_len": config.max_seq_length,
            "weight_decay": config.weight_decay,
            "warmup_ratio": config.warmup_ratio,
            "optim": config.optimizer,
            "lr_scheduler_type": config.scheduler,
            "fp16": config.fp16,
            "bf16": config.bf16,
            "gradient_checkpointing": config.gradient_checkpointing,
            "logging_steps": 10,
            "save_steps": 500,
            "save_total_limit": 3,
            "report_to": "none",
        }

        if config.finetune_method in ("lora", "qlora"):
            cfg["lora_rank"] = config.lora_rank
            cfg["lora_alpha"] = config.lora_alpha
            cfg["lora_dropout"] = config.lora_dropout
            cfg["lora_target"] = config.lora_target

        if config.finetune_method == "qlora":
            cfg["quantization_bit"] = 4

        return cfg

    @staticmethod
    def _start_log_closer(process: subprocess.Popen, log_file) -> None:  # type: ignore[type-arg]
        """守护线程：等待子进程结束后关闭日志文件句柄。"""
        import threading

        def _wait_and_close():
            process.wait()
            log_file.close()

        t = threading.Thread(target=_wait_and_close, daemon=True)
        t.start()

    @staticmethod
    def _detect_template(model_name: str) -> str:
        """根据模型名称推断对话模板。"""
        name_lower = model_name.lower()
        if "qwen" in name_lower:
            return "qwen"
        if "llama" in name_lower:
            return "llama3"
        if "chatglm" in name_lower:
            return "chatglm3"
        if "baichuan" in name_lower:
            return "baichuan2"
        return "default"

    def get_job_status(self, job_id: str) -> dict[str, Any]:
        """读取训练任务状态（日志、PID、trainer_state.json）。"""
        job_dir = self._job_dir / job_id
        if not job_dir.exists():
            return {"error": f"Job not found: {job_id}"}

        result: dict[str, Any] = {"job_id": job_id}

        pid_path = job_dir / "pid"
        if pid_path.exists():
            pid = int(pid_path.read_text().strip())
            result["pid"] = pid
            try:
                os.kill(pid, 0)
                result["running"] = True
            except (ProcessLookupError, PermissionError):
                result["running"] = False

        output_dir = job_dir / "output"
        trainer_state = output_dir / "trainer_state.json"
        if trainer_state.exists():
            try:
                state = json.loads(trainer_state.read_text(encoding="utf-8"))
                log_history = state.get("log_history", [])
                if log_history:
                    latest = log_history[-1]
                    result["current_step"] = latest.get("step", 0)
                    result["loss"] = latest.get("loss")
                    result["learning_rate"] = latest.get("learning_rate")
                result["total_steps"] = state.get("max_steps", 0)
                result["epoch"] = state.get("epoch", 0)
            except Exception as exc:
                _logger.warning("[Training] 读取 trainer_state 失败: %s", exc)

        return result
