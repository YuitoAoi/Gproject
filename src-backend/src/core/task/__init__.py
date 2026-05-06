from pydantic import BaseModel
from datetime import datetime


class TaskConfigBase(BaseModel):
    name: str | None
    desc: str | None
    config: dict


class LlamaFactoryTask(BaseModel):
    """
    task_type 类型如下:
        UNKNOWN_TASK_TYPE = 0 未知类型\n
        DATASET_GENERATE = 1  数据集处理\n
        LORA_MERGE = 2        Lora 权重合并\n
        LORA_TRAIN = 3        Lora 训练\n
        MODEL_TRAIN = 4       模型训练\n
        MODEL_INFERENCE = 5     模型推理服务
    """

    id: int
    task_type: int = 0
    config: TaskConfigBase
    created_at: datetime = datetime.now()
