"""任务记录实体 —— 清洗/训练/推理/导出任务的通用模型。"""
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class TaskRecord(BaseModel):
    id: Optional[int] = None
    owner_id: int
    task_name: str
    task_type: str = "cleaning"
    status: str = "pending"
    progress: float = 0.0
    phase: str = ""
    config: str = "{}"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @property
    def config_dict(self) -> Dict[str, Any]:
        import json
        return json.loads(self.config) if self.config else {}

    @staticmethod
    def config_to_json(d: Optional[Dict[str, Any]]) -> str:
        import json
        return json.dumps(d, ensure_ascii=False) if d else "{}"
