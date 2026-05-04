from typing import List, Optional
import abc

from src.core.dataset import Dataset
class DatasetRepository(abc.ABC):

    @abc.abstractmethod
    def create(self, dataset: Dataset) -> Optional[Exception]:
        pass

    @abc.abstractmethod
    def find(self, id: int) -> Optional[Dataset]:
        pass

    @abc.abstractmethod
    def find_by_owner(self, owner_id: int) -> List[Dataset]:
        pass

    @abc.abstractmethod
    def find_all(self) -> List[Dataset]:
        pass

    @abc.abstractmethod
    def exists(self, id: int) -> bool:
        pass

    @abc.abstractmethod
    def update(self, id: int, dataset: Dataset) -> Optional[Exception]:
        pass

    @abc.abstractmethod
    def remove(self, id: int) -> Optional[Exception]:
        pass

    @abc.abstractmethod
    def remove_batch(self,ids: List[int]) -> Optional[List[Exception]]:
        pass