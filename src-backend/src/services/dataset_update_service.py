"""数据集更新服务：name / desc / tag_ids 可编辑，meta 不可编辑。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from src.services.interfaces.dataset_repository import DatasetRepository


class DatasetUpdateRequest(BaseModel):
    """数据集更新请求。仅传要修改的字段。"""

    dataset_id: int
    name: str | None = Field(None, min_length=1, max_length=100)
    desc: str | None = Field(None, max_length=500)
    tag_ids: list[int] | None = None


class DatasetUpdateResponse(BaseModel):
    success: bool = False
    error: str | None = None


class DatasetAddTagsBatchRequest(BaseModel):
    dataset_ids: list[int]
    tag_ids: list[int]


class DatasetAddTagsBatchResponse(BaseModel):
    success: bool = False
    error: str | None = None


class DatasetUpdateService:
    """数据集更新服务。"""

    def __init__(self, dataset_repo: DatasetRepository) -> None:
        self._repo = dataset_repo

    def execute(
        self, request: DatasetUpdateRequest, owner_id: int
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

        try:
            if ds.id is None:
                raise ValueError("Dataset id cannot be None!")
            ds.updated_at = datetime.now()
            self._repo.update(ds.id, ds)
        except Exception as e:
            return DatasetUpdateResponse(error=f"Failed to update dataset: {e}")
        return DatasetUpdateResponse(success=True)


class DatasetAddTagsBatchService:
    """批量添加标签：对多个数据集追加相同标签（已存在的跳过）。"""

    def __init__(self, dataset_repo: DatasetRepository) -> None:
        self._repo = dataset_repo

    def execute(
        self, request: DatasetAddTagsBatchRequest, owner_id: int
    ) -> DatasetAddTagsBatchResponse:
        if not request.dataset_ids:
            return DatasetAddTagsBatchResponse(error="No dataset IDs provided")
        if not request.tag_ids:
            return DatasetAddTagsBatchResponse(error="No tag IDs provided")

        errs: list[str] = []
        for ds_id in request.dataset_ids:
            try:
                ds = self._repo.find_by_id(ds_id)
                if ds is None:
                    errs.append(f"Dataset not found: {ds_id}")
                    continue
                if ds.owner_id != owner_id:
                    errs.append(f"Dataset does not belong to this user: {ds_id}")
                    continue

                new_tags = [t for t in request.tag_ids if t not in ds.tag_ids]
                if ds.id is None:
                    raise ValueError("Dataset id cannot be None!")
                if new_tags:
                    ds.tag_ids.extend(new_tags)
                    self._repo.update(ds.id, ds)
            except Exception as e:
                errs.append(f"Failed to update dataset {ds_id}: {e}")

        if errs:
            return DatasetAddTagsBatchResponse(
                success=False,
                error="; ".join(errs),
            )
        return DatasetAddTagsBatchResponse(success=True)
