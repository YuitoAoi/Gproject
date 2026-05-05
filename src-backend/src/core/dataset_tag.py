from datetime import datetime
from uuid import UUID
from .entity_base import EntityBase


class DatasetTag(EntityBase):
    id: UUID
    owner_id: UUID
    name: str
    color: str
    description: str
    created_at: datetime
