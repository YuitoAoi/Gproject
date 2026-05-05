from datetime import datetime
import re
import uuid

from pydantic import BaseModel, Field, field_validator

from src.services.interfaces.dataset_repository import DatasetRepository
from src.services.interfaces.dataset_tag_repository import DatasetTagRepository

from src.core import DatasetTag

# ── 请求 / 响应模型 ──────────────────────────────────────────


class DatasetTagInfoGetRequest(BaseModel):
    """tag 详情获取请求，tag_id 由路由层传入。owner_id 由 token 注入。"""

    tag_id: uuid.UUID


class DatasetTagInfoGetResponse(BaseModel):
    success: bool
    error: str | None = None
    tag_id: uuid.UUID
    tag_name: str
    tag_color: str
    tag_desc: str
    tag_created_at: str


class DatasetTagsGetResponse(BaseModel):
    """获取属于用户的所有 tags。"""

    success: bool
    error: str | None = None
    tags: list[DatasetTagInfoGetResponse] = []


_HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


class DatasetTagCreateRequest(BaseModel):
    """创建标签请求。owner_id 由路由层从 token 注入。"""

    name: str = Field(..., min_length=1, max_length=50)
    color: str = Field(default="#808080", min_length=7, max_length=7)
    desc: str = Field(default="", max_length=200)

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str) -> str:
        if not _HEX_COLOR.match(v):
            raise ValueError("Color must be in #RRGGBB format")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if re.search(r"[\s'\"]", v):
            raise ValueError("Name contains invalid characters")
        return v


class DatasetTagCreateResponse(BaseModel):
    success: bool
    error: str | None = None


class DatasetTagDeleteRequest(BaseModel):
    """删除标签请求。"""

    tag_id: uuid.UUID
    force: bool = False


class DatasetTagDeleteResponse(BaseModel):
    success: bool
    error: str | None = None


class DatasetTagUpdateRequest(BaseModel):
    """更新标签请求。只需传要修改的字段，未传的字段保持不变。"""

    tag_id: uuid.UUID
    tag_name: str | None = None
    tag_color: str | None = None
    tag_desc: str | None = None


class DatasetTagUpdateResponse(BaseModel):
    success: bool
    error: str | None = None


# ── 服务 ─────────────────────────────────────────────────────


class DatasetTagService:
    """数据集标签服务。

    依赖通过构造函数注入，每个方法对应一个用例。
    """

    def __init__(
        self,
        dataset_tag_repo: DatasetTagRepository,
        dataset_repo: DatasetRepository,
    ) -> None:
        self._repo = dataset_tag_repo
        self._dataset_repo = dataset_repo

    # ── 获取单个 tag ──────────────────────────────────────

    def get_tag(
        self, owner_id: uuid.UUID, tag_id: uuid.UUID
    ) -> DatasetTagInfoGetResponse:
        tag = self._repo.find_by_id(tag_id)
        if tag is None or tag.owner_id != owner_id:
            return DatasetTagInfoGetResponse(
                success=False,
                error="Tag not found",
                tag_id=tag_id,
                tag_name="",
                tag_color="",
                tag_desc="",
                tag_created_at="",
            )
        return DatasetTagInfoGetResponse(
            success=True,
            tag_id=tag.id,
            tag_name=tag.name,
            tag_color=tag.color,
            tag_desc=tag.description,
            tag_created_at=tag.created_at.isoformat(),
        )

    # ── 获取用户全部 tag ──────────────────────────────────

    def get_tags(self, owner_id: uuid.UUID) -> DatasetTagsGetResponse:
        tags = self._repo.find_by_owner(owner_id)
        return DatasetTagsGetResponse(
            success=True,
            tags=[
                DatasetTagInfoGetResponse(
                    success=True,
                    tag_id=t.id,
                    tag_name=t.name,
                    tag_color=t.color,
                    tag_desc=t.description,
                    tag_created_at=t.created_at.isoformat(),
                )
                for t in tags
            ],
        )

    # ── 创建 tag ──────────────────────────────────────────
    def create_tag(
        self, request: DatasetTagCreateRequest, owner_id: uuid.UUID
    ) -> DatasetTagCreateResponse:
        try:
            self._repo.create(
                tag=DatasetTag(
                    id=uuid.uuid4(),
                    owner_id=owner_id,
                    name=request.name,
                    color=request.color,
                    description=request.desc,
                    created_at=datetime.now(),
                )
            )
            return DatasetTagCreateResponse(success=True)
        except Exception as e:
            return DatasetTagCreateResponse(success=False, error=str(e))

    # ── 更新 tag ──────────────────────────────────────────

    def update_tag(
        self, request: DatasetTagUpdateRequest, owner_id: uuid.UUID
    ) -> DatasetTagUpdateResponse:
        tag = self._repo.find_by_id(request.tag_id)
        if tag is None or tag.owner_id != owner_id:
            return DatasetTagUpdateResponse(
                success=False,
                error="Tag not found",
            )

        # 若修改 name，检查同用户下是否重名
        if request.tag_name is not None and request.tag_name != tag.name:
            existing = self._repo.find_by_name(owner_id, request.tag_name)
            if existing is not None:
                return DatasetTagUpdateResponse(
                    success=False,
                    error=f"Tag name already exists for this user: {request.tag_name}",
                )
            tag.name = request.tag_name
        if request.tag_color is not None:
            tag.color = request.tag_color
        if request.tag_desc is not None:
            tag.description = request.tag_desc

        try:
            self._repo.update_tag(tag.id, tag)
        except ValueError as e:
            return DatasetTagUpdateResponse(success=False, error=str(e))
        return DatasetTagUpdateResponse(success=True)

    # ── 删除 tag ──────────────────────────────────────────

    def delete_tag(
        self, owner_id: uuid.UUID, tag_id: uuid.UUID, force: bool = False
    ) -> DatasetTagDeleteResponse:
        tag = self._repo.find_by_id(tag_id)
        if tag is None or tag.owner_id != owner_id:
            return DatasetTagDeleteResponse(
                success=False,
                error="Tag not found",
            )

        datasets = self._dataset_repo.find_by_owner(owner_id)
        ref_datasets = [d for d in datasets if tag_id in d.tag_ids]

        if ref_datasets:
            if not force:
                names = [d.name for d in ref_datasets]
                return DatasetTagDeleteResponse(
                    success=False,
                    error=f"Tag is referenced by: {', '.join(names)}",
                )
            for ds in ref_datasets:
                ds.tag_ids = [tid for tid in ds.tag_ids if tid != tag_id]
                self._dataset_repo.update(ds.id, ds)

        try:
            self._repo.delete_tag(tag_id)
        except ValueError as e:
            return DatasetTagDeleteResponse(success=False, error=str(e))
        return DatasetTagDeleteResponse(success=True)
