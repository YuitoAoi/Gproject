# ruff: noqa: RUF002
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class DatasetMeta(BaseModel):
    """数据集元信息。"""

    format: Literal["txt", "md", "csv", "xlsx", "json", "jsonl"] = Field(..., description="数据格式")
    file_path: str
    file_size: int
    output_path: str | None = None
    log_path: str | None = None

    # ── 序列化 ──────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        """转为普通 dict。"""
        return self.model_dump()

    def to_json(self, *, indent: int | None = None) -> str:
        """转为 JSON 字符串。"""
        return self.model_dump_json(indent=indent)

    # ── 反序列化 ────────────────────────────────────────────

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DatasetMeta:
        """从 dict 构建实例，自动校验。"""
        return cls.model_validate(data)

    @classmethod
    def from_json(cls, data: str) -> DatasetMeta:
        """从 JSON 字符串构建实例，自动校验。"""
        return cls.model_validate_json(data)


class Dataset(BaseModel):
    """数据集实体。"""

    id: int | None = None
    owner_id: int
    name: str
    desc: str | None = None
    meta: DatasetMeta
    status: int
    tag_ids: list[int] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    # ── 序列化 ──────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        """转为普通 dict（含嵌套 meta）。"""
        return self.model_dump()

    def to_json(self, *, indent: int | None = None) -> str:
        """转为 JSON 字符串。"""
        return self.model_dump_json(indent=indent)

    # ── 反序列化 ────────────────────────────────────────────

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Dataset:
        """从 dict 构建实例，自动校验嵌套的 meta。"""
        return cls.model_validate(data)

    @classmethod
    def from_json(cls, data: str) -> Dataset:
        """从 JSON 字符串构建实例，自动校验。"""
        return cls.model_validate_json(data)

    # ── 工厂方法 ────────────────────────────────────────────

    @classmethod
    def new(
        cls,
        *,
        owner_id: int,
        name: str,
        meta: DatasetMeta,
        desc: str | None = None,
        status: int = 0,
        tag_ids: list[int] | None = None,
    ) -> Dataset:
        """创建新数据集，自动填充 id 与时间戳。"""
        now = datetime.now()
        return cls(
            owner_id=owner_id,
            name=name,
            desc=desc,
            meta=meta,
            status=status,
            tag_ids=tag_ids or [],
            created_at=now,
            updated_at=now,
        )
