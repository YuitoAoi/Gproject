"""任务记录实体 —— 清洗/训练/推理/导出任务的通用模型。"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

TASK_TYPE = Literal["upload", "cleaning", "training", "inference", "export"]
TASK_STATUS = Literal["pending", "running", "done", "failed", "cancelled"]


class TaskRecord(BaseModel):
    id: int | None = None
    owner_id: int
    task_name: str
    task_type: TASK_TYPE = "cleaning"
    status: TASK_STATUS = "pending"
    progress: float = 0.0
    phase: str = ""
    config: str = "{}"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @property
    def config_dict(self) -> dict[str, Any]:
        import json

        return json.loads(self.config) if self.config else {}

    @staticmethod
    def config_to_json(d: dict[str, Any] | None) -> str:
        import json

        return json.dumps(d, ensure_ascii=False) if d else "{}"
