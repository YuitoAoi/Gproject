from datetime import datetime

from pydantic import BaseModel


class DatasetTag(BaseModel):
    id: int
    owner_id: int
    name: str
    color: str
    description: str
    created_at: datetime
