"""数据集处理服务：样本预览、图生成任务提交/查询/取消、文件下载。"""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field

from src.services.interfaces.dataset_repository import DatasetRepository
from src.services.interfaces.file_repository import FileRepository

if TYPE_CHECKING:
    from src.adapters.graphgen_client import GraphGenClient


# ══════════════════════════════════════════════════════════
# 样本预览
# ══════════════════════════════════════════════════════════


class SampleRequest(BaseModel):
    """样本预览请求"""

    dataset_id: int
    limit: int = Field(default=100, ge=1, le=200, description="返回行数上限")


class SampleResponse(BaseModel):
    """样本预览响应"""

    columns: List[str] = Field(default_factory=list, description="表头列名列表")
    rows: List[Dict[str, Any]] = Field(default_factory=list, description="样本数据行")
    total_rows: int = Field(default=0, description="文件总行数")
    error: Optional[str] = None


# ══════════════════════════════════════════════════════════
# 图生成任务
# ══════════════════════════════════════════════════════════


class DatasetProcessRequest(BaseModel):
    dataset_id: int
    """图生成任务请求。input_file 由 service 层根据 dataset_id 自动填入。"""
    model_config = {"extra": "forbid"}

    # LLM
    api_key: str
    synthesizer_url: str
    synthesizer_model: str
    mode: Literal[
        "atomic",
        "multi_hop",
        "aggregated",
        "CoT",
        "multi_choice",
        "multi_answer",
        "fill_in_blank",
        "true_false",
    ]
    data_format: Literal["Alpaca", "Sharegpt", "ChatML"]

    # Optional with defaults
    tokenizer: str = "cl100k_base"
    trainee_model: Optional[str] = None
    trainee_url: Optional[str] = None
    trainee_api_key: Optional[str] = None
    chunk_size: int = Field(default=1024, gt=0)
    chunk_overlap: int = Field(default=100, ge=0)
    quiz_samples: int = Field(default=2, ge=0)
    partition_method: Literal["dfs", "bfs", "leiden", "ece"] = "ece"
    dfs_max_units: int = 5
    bfs_max_units: int = 5
    leiden_max_size: int = 20
    leiden_use_lcc: bool = False
    leiden_random_seed: int = 42
    ece_max_units: int = 20
    ece_min_units: int = 3
    ece_max_tokens: int = 10240
    ece_unit_sampling: Literal["random", "max_loss", "min_loss"] = "random"
    rpm: int = Field(default=1000, gt=0)
    tpm: int = Field(default=50000, gt=0)


class DatasetProcessResponse(BaseModel):
    """图生成任务状态响应"""

    job_id: str
    status: Literal["pending", "running", "done", "failed", "cancelled"]
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    error: Optional[str] = None
    output_path: Optional[str] = None


# ══════════════════════════════════════════════════════════
# 服务
# ══════════════════════════════════════════════════════════


class DatasetProcessService:
    """数据集处理服务。

    依赖通过构造函数注入。
    """

    def __init__(
        self,
        dataset_repo: DatasetRepository,
        file_repo: FileRepository,
        gg_client: GraphGenClient,
        celery_client=None,
    ) -> None:
        self._dataset_repo = dataset_repo
        self._file_repo = file_repo
        self._gg = gg_client
        self._celery = celery_client

    # ── 样本预览 ──────────────────────────────────────────────

    def get_sample(self, request: SampleRequest) -> SampleResponse:
        """读取数据集文件，返回前 N 条样本及表头。"""
        ds = self._dataset_repo.find_by_id(request.dataset_id)
        if ds is None:
            return SampleResponse(error=f"Dataset not found: {request.dataset_id}")

        file_path = ds.meta.file_path
        if not self._file_repo.exists(file_path):
            return SampleResponse(error=f"File not found: {file_path}")

        fmt = ds.meta.format
        try:
            if fmt == "csv":
                return self._sample_csv(file_path, request.limit)
            elif fmt in ("json", "jsonl"):
                return self._sample_jsonl(file_path, request.limit)
            elif fmt == "xlsx":
                return self._sample_xlsx(file_path, request.limit)
            else:
                return SampleResponse(error=f"Unsupported format: {fmt}")
        except Exception as exc:
            return SampleResponse(error=f"Sample read error: {exc}")

    # ── 图生成任务 ────────────────────────────────────────────

    def process(self, request: DatasetProcessRequest) -> DatasetProcessResponse:
        """提交图生成任务到 GraphGen。仅 status=0（未处理）的数据集可提交。"""
        ds = self._dataset_repo.find_by_id(request.dataset_id)
        if ds is None:
            return DatasetProcessResponse(
                job_id="",
                status="failed",
                error=f"Dataset not found: {request.dataset_id}",
            )

        if ds.status != 0:
            return DatasetProcessResponse(
                job_id="",
                status="failed",
                error=f"Dataset already processed (status={ds.status})",
            )

        file_path = ds.meta.file_path
        if not self._file_repo.exists(file_path):
            return DatasetProcessResponse(
                job_id="",
                status="failed",
                error=f"File not found: {file_path}",
            )

        input_file = Path(file_path).name
        payload = request.model_dump(exclude={"dataset_id"})
        payload["input_file"] = input_file

        resp = self._gg.submit_job(payload)
        if resp.is_error:
            return DatasetProcessResponse(
                job_id="",
                status="failed",
                error=self._parse_error(resp),
            )

        data = resp.json()
        job_id = data.get("job_id", "")

        # 提交 Celery 异步监控（Celery 不可用时不影响任务提交）
        if job_id and self._celery is not None:
            try:
                self._celery.send_task(
                    "dataset.monitor_graphgen",
                    kwargs={"job_id": job_id, "dataset_id": request.dataset_id},
                )
            except Exception:
                pass

        return DatasetProcessResponse(
            job_id=job_id,
            status=data.get("status", "pending"),
        )

    def check_job(self, job_id: str, dataset_id: int) -> DatasetProcessResponse:
        """查询 GraphGen 任务状态，完成后自动更新数据集 status 和 output_path。

        status 流转: 0(未处理) → 1(处理中/已提交) → 2(已完成) / -1(失败)
        """
        result = self.get_job(job_id)
        ds = self._dataset_repo.find_by_id(dataset_id)
        if ds is None:
            return result

        if result.status in ("pending", "running") and ds.status == 0:
            ds.status = 1
            self._dataset_repo.update(dataset_id, ds)
        elif result.status == "done":
            ds.status = 2
            if result.output_path:
                ds.meta.file_path = result.output_path
            self._dataset_repo.update(dataset_id, ds)
        elif result.status == "failed":
            ds.status = -1
            self._dataset_repo.update(dataset_id, ds)

        return result

    def get_job(self, job_id: str) -> DatasetProcessResponse:
        """查询 GraphGen 任务状态。"""
        resp = self._gg.get_job(job_id)
        if resp.is_error:
            return DatasetProcessResponse(
                job_id=job_id,
                status="failed",
                error=self._parse_error(resp),
            )

        data = resp.json()
        return DatasetProcessResponse(
            job_id=data.get("job_id", job_id),
            status=data.get("status", "unknown"),
            created_at=data.get("created_at"),
            started_at=data.get("started_at"),
            finished_at=data.get("finished_at"),
            progress=data.get("progress", 0.0),
            error=data.get("error"),
            output_path=data.get("output_path"),
        )

    def cancel_job(self, job_id: str) -> DatasetProcessResponse:
        """取消 GraphGen 任务。"""
        resp = self._gg.cancel_job(job_id)
        if resp.is_error:
            return DatasetProcessResponse(
                job_id=job_id,
                status="failed",
                error=self._parse_error(resp),
            )

        data = resp.json()
        return DatasetProcessResponse(
            job_id=data.get("job_id", job_id),
            status=data.get("status", "cancelled"),
        )

    # ── 内部 ──────────────────────────────────────────────────

    @staticmethod
    def _parse_error(resp) -> str:
        """从 httpx Response 提取错误信息。"""
        try:
            detail = resp.json()
            if isinstance(detail, dict):
                return detail.get("detail", resp.text)
            if isinstance(detail, list):
                return "; ".join(
                    d.get("msg", str(d)) for d in detail if isinstance(d, dict)
                )
            return str(detail)
        except Exception:
            return resp.text or f"HTTP {resp.status_code}"

    # ── 样本读取 ──────────────────────────────────────────────

    def _sample_csv(self, file_path: str, limit: int) -> SampleResponse:
        raw = self._file_repo.read(file_path)
        reader = csv.reader(io.StringIO(raw.decode("utf-8")))
        try:
            columns = next(reader)
        except StopIteration:
            return SampleResponse(columns=[], rows=[], total_rows=0)

        rows: List[Dict[str, Any]] = []
        total = 0
        for row in reader:
            total += 1
            if len(rows) < limit:
                rows.append(
                    {
                        col: row[i] if i < len(row) else ""
                        for i, col in enumerate(columns)
                    }
                )
        return SampleResponse(
            columns=columns,
            rows=rows,
            total_rows=total + 1,  # +1 for header
        )

    def _sample_jsonl(self, file_path: str, limit: int) -> SampleResponse:
        raw = self._file_repo.read(file_path)
        lines = raw.decode("utf-8").strip().splitlines()
        rows: List[Dict[str, Any]] = []
        columns: List[str] = []
        for line in lines:
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    rows.append(obj)
                    for k in obj:
                        if k not in columns:
                            columns.append(k)
                    if len(rows) >= limit:
                        break
            except json.JSONDecodeError:
                continue
        return SampleResponse(
            columns=columns,
            rows=rows[:limit],
            total_rows=len(lines),
        )

    def _sample_xlsx(self, file_path: str, limit: int) -> SampleResponse:
        raw = self._file_repo.read(file_path)
        from openpyxl import load_workbook

        wb = load_workbook(io.BytesIO(raw), read_only=True)
        ws = wb.active
        if ws is None:
            wb.close()
            return SampleResponse(columns=[], rows=[], total_rows=0)
        rows_iter = ws.iter_rows(values_only=True)

        try:
            columns = [str(c) if c is not None else "" for c in next(rows_iter)]
        except StopIteration:
            wb.close()
            return SampleResponse(columns=[], rows=[], total_rows=0)

        rows: List[Dict[str, Any]] = []
        total = 0
        for row in rows_iter:
            total += 1
            if len(rows) < limit:
                rows.append(
                    {
                        col: (row[i] if i < len(row) else "")
                        for i, col in enumerate(columns)
                    }
                )
        wb.close()
        return SampleResponse(
            columns=columns,
            rows=rows,
            total_rows=total + 1,
        )
