"""数据集处理服务：样本预览、清洗配置、异步任务触发、文件下载。"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from src.services.interfaces.dataset_repository import DatasetRepository
from src.services.interfaces.file_repository import FileRepository


# ══════════════════════════════════════════════════════════
# 样本预览
# ══════════════════════════════════════════════════════════

class SampleRequest(BaseModel):
    """样本预览请求"""
    limit: int = Field(default=100, ge=1, le=200, description="返回行数上限")


class SampleResponse(BaseModel):
    """样本预览响应"""
    columns: List[str] = Field(default_factory=list, description="表头列名列表")
    rows: List[Dict[str, Any]] = Field(default_factory=list, description="样本数据行")
    total_rows: int = Field(default=0, description="文件总行数")
    error: Optional[str] = None


# ══════════════════════════════════════════════════════════
# 清洗配置
# ══════════════════════════════════════════════════════════

class FieldMapping(BaseModel):
    """单条字段映射：源列 → LLaMA 标准字段"""
    source_column: str = Field(..., description="源数据表头名")
    target_field: Literal["instruction", "input", "output"] = Field(
        ..., description="LLaMA-Factory 标准字段"
    )


class BasicFiltering(BaseModel):
    """基础过滤"""
    enabled: bool = False
    remove_empty: bool = Field(default=True, description="剔除空白行/缺失值")
    min_text_length: int = Field(default=10, ge=1, le=10000, description="过滤短文本（字符数）")


class TextFormatting(BaseModel):
    """文本格式化"""
    enabled: bool = False
    remove_html: bool = Field(default=True, description="移除 HTML/XML 标签")
    normalize_unicode: bool = Field(default=False, description="全角转半角")


class PiiMasking(BaseModel):
    """隐私脱敏"""
    enabled: bool = False
    phone: bool = Field(default=True, description="手机号码脱敏")
    id_card: bool = Field(default=False, description="身份证号脱敏")
    email: bool = Field(default=False, description="电子邮箱脱敏")
    bank_card: bool = Field(default=False, description="银行卡号脱敏")


class Deduplication(BaseModel):
    """语料去重"""
    enabled: bool = False
    method: Literal["exact", "minhash"] = Field(default="minhash")
    threshold: float = Field(default=0.85, ge=0.5, le=1.0, description="MinHash 相似度阈值")


class CleanConfig(BaseModel):
    """清洗编排完整配置"""
    field_mapping: List[FieldMapping] = Field(
        default_factory=list, description="字段映射列表"
    )
    basic_filtering: BasicFiltering = Field(default_factory=BasicFiltering)
    text_formatting: TextFormatting = Field(default_factory=TextFormatting)
    pii_masking: PiiMasking = Field(default_factory=PiiMasking)
    deduplication: Deduplication = Field(default_factory=Deduplication)


class ProcessRequest(BaseModel):
    """处理请求 —— 包含清洗或转换的全部配置"""
    # 处理类型
    process_type: Literal["clean", "convert"] = Field(..., description="clean=数据清洗 / convert=格式转换")

    # 清洗配置（process_type=clean 时使用）
    clean_config: Optional[CleanConfig] = Field(None, description="清洗编排配置")

    # 格式转换配置（process_type=convert 时使用）
    convert_format: Optional[Literal["alpaca", "sharegpt"]] = Field(
        None, description="转换目标格式"
    )


class ProcessResponse(BaseModel):
    """处理任务响应"""
    task_id: Optional[str] = Field(None, description="Celery 异步任务 ID")
    status: str = Field(default="pending", description="pending / running / completed / failed")
    message: str = ""
    error: Optional[str] = None


# ══════════════════════════════════════════════════════════
# 文件下载
# ══════════════════════════════════════════════════════════

class DownloadResponse(BaseModel):
    """下载响应（元数据，实际文件通过 StreamingResponse 返回）"""
    filename: str = ""
    file_size: int = 0
    format: str = ""
    error: Optional[str] = None


# ══════════════════════════════════════════════════════════
# 服务实现
# ══════════════════════════════════════════════════════════

class DatasetProcessService:
    """数据集处理服务 —— 样本预览 + 清洗/转换触发。"""

    def __init__(
        self,
        dataset_repo: DatasetRepository,
        file_repo: FileRepository,
    ) -> None:
        self._dataset_repo = dataset_repo
        self._file_repo = file_repo

    def get_sample(
        self, dataset_id: int, request: SampleRequest
    ) -> SampleResponse:
        """获取数据集的前 N 条样本及表头。

        TODO: 实现从 file_repo 读取 csv/xlsx/json 文件并解析前 N 行。
        """
        ds = self._dataset_repo.find(dataset_id)
        if ds is None:
            return SampleResponse(error=f"Dataset not found: {dataset_id}")

        # TODO: 根据 ds.meta.format 选择解析方式
        # - csv: pd.read_csv(file_path, nrows=limit)
        # - xlsx: pd.read_excel(file_path, nrows=limit)
        # - json: json.load + 切片
        return SampleResponse(
            columns=[],
            rows=[],
            total_rows=0,
            error="Sample preview not yet implemented",
        )

    def process(
        self, dataset_id: int, request: ProcessRequest
    ) -> ProcessResponse:
        """提交清洗/转换任务到 Celery。"""
        ds = self._dataset_repo.find(dataset_id)
        if ds is None:
            return ProcessResponse(error=f"Dataset not found: {dataset_id}")

        if request.process_type == "clean" and request.clean_config is None:
            return ProcessResponse(error="clean_config is required for clean process_type")

        if request.process_type == "convert" and request.convert_format is None:
            return ProcessResponse(error="convert_format is required for convert process_type")

        # 延迟导入，服务层不直接依赖 infrastructure
        from src.tasks.dataset_tasks import dataset_clean, dataset_convert

        if request.process_type == "clean":
            task = dataset_clean.delay(dataset_id, request.model_dump())
        else:
            task = dataset_convert.delay(dataset_id, request.convert_format)

        return ProcessResponse(
            task_id=task.id,
            status="pending",
            message=f"{request.process_type} task started",
        )

    def download(self, dataset_id: int) -> DownloadResponse:
        """获取数据集文件的下载信息。

        TODO: 返回文件元数据，实际下载通过路由层的 FileResponse 实现。
        """
        ds = self._dataset_repo.find(dataset_id)
        if ds is None:
            return DownloadResponse(error=f"Dataset not found: {dataset_id}")

        return DownloadResponse(
            filename=f"{ds.name}.{ds.meta.format}",
            file_size=ds.meta.file_size,
            format=ds.meta.format,
        )
