"""数据集删除服务。"""

from __future__ import annotations

from typing import List

from pydantic import BaseModel

from src.services.interfaces.dataset_repository import DatasetRepository
from src.services.interfaces.file_repository import FileRepository

# ══════════════════════════════════════════════════════════
# 模型
# ══════════════════════════════════════════════════════════


class DatasetRemoveRequest(BaseModel):
    """删除请求：支持单条或批量。"""

    dataset_ids: List[int]


class DatasetRemoveResponse(BaseModel):
    success: bool = False
    deleted: List[int] = []
    errors: List[str] = []


# ══════════════════════════════════════════════════════════
# 服务
# ══════════════════════════════════════════════════════════


class DatasetRemoveService:
    """数据集删除服务。

    流程：校验归属 → 删除文件 → 批量删除 DB 记录。
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
        self, request: DatasetRemoveRequest, owner_id: int
    ) -> DatasetRemoveResponse:
        if not request.dataset_ids:
            return DatasetRemoveResponse(success=True)

        deleted: List[int] = []
        errs: List[str] = []

        for ds_id in request.dataset_ids:
            ds = self._dataset_repo.find_by_id(ds_id)
            if ds is None:
                errs.append(f"Dataset not found: {ds_id}")
                continue
            if ds.owner_id != owner_id:
                errs.append(f"Dataset does not belong to this user: {ds_id}")
                continue

            # 先删除 DB 记录，再清理文件（避免幽灵记录）
            err = self._dataset_repo.remove(ds_id)
            if err is not None:
                errs.append(f"Failed to remove dataset {ds_id}: {err}")
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
