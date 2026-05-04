import abc
from typing import List, Optional

from src.core.dataset_tag import DatasetTag
class DatasetTagRepository(abc.ABC):
    
    @abc.abstractmethod
    def create(
        self,
        name: str,
        color: str,
        desc: str,
        owner: int
        ) -> Optional[Exception]:
        pass

    @abc.abstractmethod
    def find_by_id(self, tag_id: int) -> Optional[DatasetTag]:
        pass

    @abc.abstractmethod
    def find_by_name(self, owner_id: int, name: str) -> Optional[DatasetTag]:
        pass

    @abc.abstractmethod
    def find_by_owner(self, owner_id: int) -> List[DatasetTag]:
        pass

    @abc.abstractmethod
    def find_all(self) -> List[DatasetTag]:
        pass

    @abc.abstractmethod
    def update_tag(self,tag_id: int, tag: DatasetTag) -> Optional[Exception]:
        pass

    @abc.abstractmethod
    def delete_tag(self,tag_id: int) -> Optional[Exception]:
        pass