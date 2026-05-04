
import abc
from typing import Optional
import uuid

from pydantic import BaseModel

class DatasetGenerateConfig(BaseModel):
    pass

class DatasetGenerator(abc.ABC):
    
    @abc.abstractmethod
    def generate(self,config: DatasetGenerateConfig) -> uuid.UUID:
        pass
    
    @abc.abstractmethod
    def cancel_task(self) -> Optional[Exception]:
        pass
    
    def check_validate(
        self, base_url: str,
        api_key: str ,model_id: str = "Qwen/Qwen2.5-7B-Instruct") -> bool:
        pass