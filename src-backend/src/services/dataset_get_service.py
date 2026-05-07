from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from src.core.dataset import Dataset
from src.services.interfaces.dataset_repository import DatasetRepository


class DatasetItemDTO(BaseModel):
    """数据集列表项 DTO，不暴露 file_path、owner_id 等内部字段。"""

    id: int
    name: str
    desc: Optional[str] = None
    format: str
    file_size: int
    status: int
    tag_ids: List[int] = []
    created_at: datetime
    updated_at: datetime


class GetDatasetsResponse(BaseModel):
    items: List[DatasetItemDTO]
    total: int
    error: Optional[str] = None


class GetDatasetResponse(BaseModel):
    dataset: Optional[DatasetItemDTO] = None
    error: Optional[str] = None


class GetDatasetsService:
    """数据集查询服务。"""

    def __init__(
        self,
        dataset_repo: DatasetRepository,
    ) -> None:
        self._dataset_repo = dataset_repo

    @staticmethod
    def _to_dto(ds: Dataset) -> DatasetItemDTO:
        return DatasetItemDTO(
            id=ds.id or 0,
            name=ds.name,
            desc=ds.desc,
            format=ds.meta.format,
            file_size=ds.meta.file_size,
            status=ds.status,
            tag_ids=ds.tag_ids,
            created_at=ds.created_at,
            updated_at=ds.updated_at,
        )

    def get_all(self, owner_id: int) -> GetDatasetsResponse:
        """返回指定用户的数据集列表。"""
        try:
            items = [
                self._to_dto(d) for d in self._dataset_repo.find_by_owner(owner_id)
            ]
            return GetDatasetsResponse(items=items, total=len(items))
        except Exception as e:
            return GetDatasetsResponse(items=[], total=0, error=str(e))

    def get_by_id(self, dataset_id: int, owner_id: int) -> GetDatasetResponse:
        """返回单个数据集详情，仅限所属用户。"""
        try:
            ds = self._dataset_repo.find_by_id(dataset_id)
            if ds is None:
                return GetDatasetResponse(error=f"Dataset not found: {dataset_id}")
            if ds.owner_id != owner_id:
                return GetDatasetResponse(
                    error=f"Access denied to dataset: {dataset_id}"
                )
            return GetDatasetResponse(dataset=self._to_dto(ds))
        except Exception as e:
            return GetDatasetResponse(error=str(e))
