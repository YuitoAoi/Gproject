"""数据集更新服务：name / desc / tag_ids 可编辑，meta 不可编辑。"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from src.services.interfaces.dataset_repository import DatasetRepository


class DatasetUpdateRequest(BaseModel):
    """数据集更新请求。仅传要修改的字段。"""

    dataset_id: uuid.UUID
    name: str | None = Field(None, min_length=1, max_length=100)
    desc: str | None = Field(None, max_length=500)
    tag_ids: list[uuid.UUID] | None = None


class DatasetUpdateResponse(BaseModel):
    success: bool = False
    error: str | None = None


class DatasetUpdateService:
    """数据集更新服务。"""

    def __init__(self, dataset_repo: DatasetRepository) -> None:
        self._repo = dataset_repo

    def execute(
        self, request: DatasetUpdateRequest, owner_id: uuid.UUID
    ) -> DatasetUpdateResponse:
        ds = self._repo.find_by_id(request.dataset_id)
        if ds is None:
            return DatasetUpdateResponse(
                error=f"Dataset not found: {request.dataset_id}"
            )
        if ds.owner_id != owner_id:
            return DatasetUpdateResponse(
                error=f"Dataset not found: {request.dataset_id}"
            )

        changed = False

        if request.name is not None and request.name != ds.name:
            ds.name = request.name
            changed = True

        if request.desc is not None and request.desc != ds.desc:
            ds.desc = request.desc
            changed = True

        if request.tag_ids is not None and request.tag_ids != ds.tag_ids:
            ds.tag_ids = request.tag_ids
            changed = True

        if not changed:
            return DatasetUpdateResponse(success=True)

        self._repo.update(ds.id, ds)
        return DatasetUpdateResponse(success=True)
