"""数据集删除服务。"""

from __future__ import annotations

import uuid

from pydantic import BaseModel

from src.services.interfaces.dataset_repository import DatasetRepository
from src.services.interfaces.file_repository import FileRepository


class DatasetRemoveRequest(BaseModel):
    """删除请求：支持单条或批量。"""

    dataset_ids: list[uuid.UUID]


class DatasetRemoveResponse(BaseModel):
    success: bool = False
    deleted: list[uuid.UUID] = []
    errors: list[str] = []


class DatasetRemoveService:
    """数据集删除服务。

    流程：校验归属 → 删除 DB 记录 → 删除文件。
    每个 dataset 独立处理，单条失败不影响其余。
    """

    def __init__(
        self,
        dataset_repo: DatasetRepository,
        file_repo: FileRepository,
    ) -> None:
        self._dataset_repo = dataset_repo
        self._file_repo = file_repo

    def execute(
        self, request: DatasetRemoveRequest, owner_id: uuid.UUID
    ) -> DatasetRemoveResponse:
        if not request.dataset_ids:
            return DatasetRemoveResponse(success=True)

        deleted: list[uuid.UUID] = []
        errs: list[str] = []

        for ds_id in request.dataset_ids:
            ds = self._dataset_repo.find_by_id(ds_id)
            if ds is None:
                errs.append(f"Dataset not found: {ds_id}")
                continue
            if ds.owner_id != owner_id:
                errs.append(f"Dataset does not belong to this user: {ds_id}")
                continue

            # 先删除 DB 记录，再清理文件（避免幽灵记录）
            try:
                self._dataset_repo.remove(ds_id)
            except Exception as exc:
                errs.append(f"Failed to remove dataset {ds_id}: {exc}")
                continue

            file_path = ds.meta.file_path
            if file_path:
                try:
                    self._file_repo.delete(file_path)
                except Exception as exc:
                    errs.append(
                        f"Dataset {ds_id} removed but file cleanup failed: {exc}"
                    )

            deleted.append(ds_id)

        return DatasetRemoveResponse(
            success=len(errs) == 0,
            deleted=deleted,
            errors=errs,
        )
