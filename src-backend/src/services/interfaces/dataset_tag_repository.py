import abc

from src.core.dataset_tag import DatasetTag


class DatasetTagRepository(abc.ABC):
    @abc.abstractmethod
    def create(self, name: str, color: str, desc: str, owner: int) -> Exception | None:
        pass

    @abc.abstractmethod
    def find_by_id(self, tag_id: int) -> DatasetTag | None:
        pass

    @abc.abstractmethod
    def find_by_name(self, owner_id: int, name: str) -> DatasetTag | None:
        pass

    @abc.abstractmethod
    def find_by_owner(self, owner_id: int) -> list[DatasetTag]:
        pass

    @abc.abstractmethod
    def find_all(self) -> list[DatasetTag]:
        pass

    @abc.abstractmethod
    def update_tag(self, tag_id: int, tag: DatasetTag) -> Exception | None:
        pass

    @abc.abstractmethod
    def delete_tag(self, tag_id: int) -> Exception | None:
        pass
