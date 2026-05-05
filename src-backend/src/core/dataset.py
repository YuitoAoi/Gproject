import uuid, enum
from msgspec.json import encode, decode
from datetime import datetime
from .entity_base import EntityBase


class DatasetFormat(enum.Enum):
    CSV = "csv"
    XLSX = "xlsx"
    JSON = "json"
    JSONL = "jsonl"


class DatasetMeta(EntityBase):
    """数据集元信息。"""

    format: DatasetFormat
    file_path: str
    file_size: int


class Dataset(EntityBase):
    """数据集实体。"""

    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    meta: DatasetMeta
    created_at: datetime
    updated_at: datetime
    desc: str | None = None
    status: int = 0
    tag_ids: list[uuid.UUID] = []
