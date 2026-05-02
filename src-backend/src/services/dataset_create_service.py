from __future__ import annotations

from typing import List, Optional
import uuid

from pydantic import BaseModel, Field

from src.core.dataset import Dataset, DatasetMeta
from src.services.interfaces.dataset_repository import DatasetRepository
from src.services.interfaces.file_repository import FileRepository


class CreateDatasetRequest(BaseModel):
    """创建数据集请求"""
    owner_id: int = Field(default=0, description="所属用户 ID（由路由层从 token 注入）")
    name: str = Field(..., min_length=1, max_length=100, description="数据集名称")
    desc: Optional[str] = Field(None, max_length=500, description="数据集描述")
    tag_ids: List[int] = Field(default_factory=list, description="标签ID")
    file_path: str


class CreateDatasetResponse(BaseModel):
    success: bool = False
    error: Optional[str] = None


class CreateDatasetService:
    """创建数据集服务。

    依赖通过构造函数注入，调用 execute() 时无需再传仓储。
    """

    def __init__(
        self,
        dataset_repo: DatasetRepository,
        file_repo: FileRepository,
    ) -> None:
        self._dataset_repo = dataset_repo
        self._file_repo = file_repo

    def execute(self, request: CreateDatasetRequest) -> CreateDatasetResponse:
        """执行数据集创建。"""
        try:
            file_path = request.file_path
            file_format = self._file_repo.get_file_ext(file_path).lstrip('.')

            if not self._file_repo.exists(file_path):
                return CreateDatasetResponse(
                    success=False,
                    error=f"File not found: {file_path}",
                )

            if file_format not in ('csv', 'xlsx', 'json'):
                return CreateDatasetResponse(
                    success=False,
                    error=f"Unsupported file type: {file_format}",
                )

            meta = DatasetMeta(
                format=file_format,
                file_path=file_path,
                file_size=self._file_repo.get_size(file_path),
            )
            entity = Dataset.new(
                owner_id=request.owner_id,
                name=request.name,
                desc=request.desc,
                meta=meta,
                tag_ids=request.tag_ids,
            )

            self._dataset_repo.create(entity)
            return CreateDatasetResponse(success=True)

        except Exception as exc:
            return CreateDatasetResponse(
                success=False,
                error=f"Internal error: {exc}",
            )
