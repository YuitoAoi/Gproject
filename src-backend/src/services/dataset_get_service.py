from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel

from src.core.dataset import Dataset
from src.services.interfaces.dataset_repository import DatasetRepository


class GetDatasetsResponse(BaseModel):
    items: List[Dataset]
    total: int
    error: Optional[str] = None


class GetDatasetResponse(BaseModel):
    dataset: Optional[Dataset] = None
    error: Optional[str] = None


class GetDatasetsService:
    """数据集查询服务。"""

    def __init__(
        self,
        dataset_repo: DatasetRepository,
    ) -> None:
        self._dataset_repo = dataset_repo

    def get_all(self, owner_id: int) -> GetDatasetsResponse:
        """返回指定用户的数据集列表。"""
        try:
            all_items = self._dataset_repo.find_all()
            items = [d for d in all_items if d.owner_id == owner_id]
            return GetDatasetsResponse(items=items, total=len(items))
        except Exception as e:
            return GetDatasetsResponse(items=[], total=0, error=str(e))

    def get_by_id(self, dataset_id: int, owner_id: int) -> GetDatasetResponse:
        """返回单个数据集详情，仅限所属用户。"""
        try:
            ds = self._dataset_repo.find(dataset_id)
            if ds is None:
                return GetDatasetResponse(error=f"Dataset not found: {dataset_id}")
            if ds.owner_id != owner_id:
                return GetDatasetResponse(error=f"Access denied to dataset: {dataset_id}")
            return GetDatasetResponse(dataset=ds)
        except Exception as e:
            return GetDatasetResponse(error=str(e))
