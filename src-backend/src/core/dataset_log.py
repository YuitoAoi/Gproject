"""数据集日志实体 —— 记录清洗任务的日志文件路径。"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DatasetLog(BaseModel):
    id: Optional[int] = None
    job_id: str
    dataset_id: int
    log_path: str
    created_at: datetime
