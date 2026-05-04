from pydantic import BaseModel
from datetime import datetime

class DatasetTag(BaseModel):
    id: int
    owner_id: int
    name: str
    color: str
    description: str
    created_at: datetime