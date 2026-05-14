"""LlamaFactory 导出客户端 — 通过 subprocess 调用 LlamaFactory CLI 导出 GGUF 等格式。"""

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


class ExportConfig(BaseModel):
    """导出任务配置参数。"""

    base_model: str
    adapter_path: str = ""
    export_path: str = ""
    export_format: str = "gguf"  # gguf | pytorch | gptq | awq | onnx
    quantization_method: str = Field(default="q4_k_m", description="Q4_K_M / Q5_K_M / Q8_0 / f16 / f32")
    tokenizer_mode: str = "llama"
    template: str = ""


class ExportResult(BaseModel):
    """导出任务提交结果。"""

    success: bool = False
    job_id: str = ""
    config_path: str = ""
    export_path: str = ""
    error: str | None = None


class LlamaFactoryExportClient:
    """通过子进程调用 LlamaFactory CLI 执行模型导出。"""

    def __init__(self) -> None:
        self._job_dir = Path(proj_config.LLAMAFACTORY_JOB_DIR)
        self._job_dir.mkdir(parents=True, exist_ok=True)
        self._data_dir = Path(proj_config.LLAMAFACTORY_DATA_DIR)
        self._export_cmd = proj_config.LLAMAFACTORY_EXPORT_COMMAND

    def submit_export(self, config: ExportConfig) -> ExportResult:
        job_id = f"export_{uuid.uuid4().hex[:12]}"
        job_dir = self._job_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        export_path = config.export_path or str(job_dir / "output" / "exported_model.gguf")
        os.makedirs(os.path.dirname(export_path), exist_ok=True)

        yaml_config = self._build_config(config, export_path)
        config_path = job_dir / "export_config.json"

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(yaml_config, f, indent=2, ensure_ascii=False)

        _logger.info("[Export] 配置已写入: %s", config_path)

        log_path = job_dir / "export.log"

        try:
            cmd = [self._export_cmd, "export", str(config_path)]
            _logger.info("[Export] 启动命令: %s", " ".join(cmd))

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

            return ExportResult(
                success=True,
                job_id=job_id,
                config_path=str(config_path),
                export_path=export_path,
            )
        except FileNotFoundError:
            msg = f"LlamaFactory CLI 未找到: {self._export_cmd}"
            _logger.error("[Export] %s", msg)
            return ExportResult(error=msg)
        except Exception as exc:
            _logger.error("[Export] 启动失败: %s", exc)
            return ExportResult(error=str(exc))

    def _build_config(self, config: ExportConfig, export_path: str) -> dict[str, Any]:
        cfg: dict[str, Any] = {
            "model_name_or_path": config.base_model,
            "adapter_name_or_path": config.adapter_path,
            "template": config.template or self._detect_template(config.base_model),
            "export_path": export_path,
            "export_format": config.export_format,
        }

        if config.export_format == "gguf" and config.quantization_method:
            qbit = self._map_quantization(config.quantization_method)
            if qbit is not None:
                cfg["quantization_bit"] = qbit

        if config.tokenizer_mode:
            cfg["tokenizer_mode"] = config.tokenizer_mode

        return cfg

    @staticmethod
    def _map_quantization(method: str) -> int | None:
        mapping = {
            "q4_k_m": 4,
            "q5_k_m": 5,
            "q8_0": 8,
            "f16": 16,
            "f32": 32,
        }
        return mapping.get(method.lower())

    @staticmethod
    def _detect_template(model_name: str) -> str:
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

    @staticmethod
    def _start_log_closer(process: subprocess.Popen, log_file) -> None:  # type: ignore[type-arg]
        import threading

        def _wait_and_close():
            process.wait()
            log_file.close()

        t = threading.Thread(target=_wait_and_close, daemon=True)
        t.start()

    def get_job_status(self, job_id: str) -> dict[str, Any]:
        job_dir = self._job_dir / job_id
        if not job_dir.exists():
            return {"error": f"Export job not found: {job_id}"}

        result: dict[str, Any] = {"job_id": job_id}

        pid_path = job_dir / "pid"
        if pid_path.exists():
            pid = int(pid_path.read_text(encoding="utf-8").strip())
            result["pid"] = pid
            try:
                os.kill(pid, 0)
                result["running"] = True
            except (ProcessLookupError, PermissionError):
                result["running"] = False

        log_path = job_dir / "export.log"
        if log_path.exists():
            result["has_log"] = True

        cfg_path = job_dir / "export_config.json"
        if cfg_path.exists():
            try:
                cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
                result["export_path"] = cfg.get("export_path", "")
                ep = cfg.get("export_path", "")
                if ep and os.path.exists(ep):
                    result["exists"] = True
                    result["file_size"] = os.path.getsize(ep)
            except Exception as exc:
                _logger.warning("[Export] 读取导出配置失败: %s", exc)

        return result