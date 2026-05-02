from __future__ import annotations

import copy
import uuid
from threading import Lock
from typing import Optional

from src.core.dataset import Dataset
from src.services.interfaces.dataset_repository import DatasetRepository


class MemoryDatasetRepoAdpter(DatasetRepository):
    """基于 dict 的内存数据集仓储实现。

    所有数据存储于进程内存中，适合开发调试与单元测试。
    内置读写锁保证 FastAPI 并发场景下的线程安全。

    使用示例::

        repo = MemoryDatasetRepoAdpter()
        ds = Dataset(id=uuid.uuid4(), name="test", ...)
        repo.create(ds)
        found = repo.find(ds.id)
    """

    def __init__(self) -> None:
        self._storage: dict[uuid.UUID, Dataset] = {}
        self._lock = Lock()

    # ── DatabaseRepository 实现 ──────────────────────────────

    def create(self, dataset: Dataset) -> uuid.UUID:
        """保存数据集实体，返回其 id。已存在同名 id 时覆盖。"""
        with self._lock:
            self._storage[dataset.id] = copy.deepcopy(dataset)
        return dataset.id

    def find(self, id: uuid.UUID) -> Optional[Dataset]:
        """按 id 查找数据集，不存在返回 None。"""
        with self._lock:
            dataset = self._storage.get(id)
            return copy.deepcopy(dataset) if dataset is not None else None

    def find_all(self) -> list[Dataset]:
        """返回所有数据集实体的深拷贝列表。"""
        with self._lock:
            return [copy.deepcopy(v) for v in self._storage.values()]

    def exists(self, id: uuid.UUID) -> bool:
        """检查指定 id 的数据集是否存在。"""
        with self._lock:
            return id in self._storage

    def update(self, id: uuid.UUID, dataset: Dataset) -> None:
        """更新数据集实体。若 id 不存在则抛出 KeyError。"""
        with self._lock:
            if id not in self._storage:
                raise KeyError(f"Dataset with id {id} not found")
            self._storage[id] = copy.deepcopy(dataset)

    def remove(self, id: uuid.UUID) -> Optional[Dataset]:
        """删除并返回被删除的数据集实体，不存在返回 None。"""
        with self._lock:
            dataset = self._storage.pop(id, None)
            return copy.deepcopy(dataset) if dataset is not None else None

    # ── 额外辅助方法 ─────────────────────────────────────────

    def count(self) -> int:
        """返回当前存储的数据集总数。"""
        with self._lock:
            return len(self._storage)

    def clear(self) -> None:
        """清空所有数据。"""
        with self._lock:
            self._storage.clear()

    def find_by_name(self, name: str) -> list[Dataset]:
        """按名称精确匹配。"""
        with self._lock:
            return [
                copy.deepcopy(v)
                for v in self._storage.values()
                if v.name == name
            ]

    def find_by_status(self, status: int) -> list[Dataset]:
        """按状态筛选。"""
        with self._lock:
            return [
                copy.deepcopy(v)
                for v in self._storage.values()
                if v.status == status
            ]

    def __repr__(self) -> str:
        with self._lock:
            return f"<MemoryDatasetRepoAdpter count={len(self._storage)}>"
