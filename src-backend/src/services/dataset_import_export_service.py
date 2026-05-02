from __future__ import annotations

import uuid
from typing import Optional, Literal

from pydantic import BaseModel

from src.services.interfaces.dataset_repository import DatasetRepository
from src.services.interfaces.file_repository import FileRepository


class ImportExportDatasetRequest(BaseModel):
    """导入导出数据集请求基类。"""
    pass


class ImportExportDatasetResponse(BaseModel):
    success: bool
    error: Optional[str] = None


class ImportDatasetService:
    """导入数据集服务。"""

    def __init__(
        self,
        dataset_repo: DatasetRepository,
        file_repo: FileRepository,
    ) -> None:
        self._dataset_repo = dataset_repo
        self._file_repo = file_repo

    def execute(
        self,
        request: ImportExportDatasetRequest,
    ) -> ImportExportDatasetResponse:
        """执行数据集导入。"""
        # TODO 后续补全导入逻辑
        return ImportExportDatasetResponse(success=False, error="Import not implemented yet")


class ExportDatasetService:
    """导出数据集服务。"""

    def __init__(
        self,
        dataset_repo: DatasetRepository,
        file_repo: FileRepository,
    ) -> None:
        self._dataset_repo = dataset_repo
        self._file_repo = file_repo

    def execute(
        self,
        dataset_id: uuid.UUID,
        target_path: str,
        as_type: Optional[Literal['csv', 'xlsx', 'json']] = None,
    ) -> ImportExportDatasetResponse:
        """执行数据集导出。"""
        dataset = self._dataset_repo.find(dataset_id)
        if dataset is None:
            return ImportExportDatasetResponse(
                success=False,
                error=f"Dataset not found: {dataset_id}",
            )

        export_format = as_type or dataset.meta.format

        # 读取源文件数据
        data = self._file_repo.read(dataset.meta.file_path)

        # 写入目标路径
        self._file_repo.over_write(target_path, data)

        return ImportExportDatasetResponse(success=True)
