import abc, uuid
from src.core import DatasetTag


class DatasetTagRepository(abc.ABC):

    @abc.abstractmethod
    def create(self, tag: DatasetTag) -> None:
        pass

    @abc.abstractmethod
    def find_by_id(self, tag_id: uuid.UUID) -> DatasetTag | None:
        pass

    @abc.abstractmethod
    def find_by_name(self, owner_id: uuid.UUID, name: str) -> DatasetTag | None:
        pass

    @abc.abstractmethod
    def find_by_owner(self, owner_id: uuid.UUID) -> list[DatasetTag]:
        pass

    @abc.abstractmethod
    def find_all(self) -> list[DatasetTag]:
        pass

    @abc.abstractmethod
    def update_tag(self, tag_id: uuid.UUID, tag: DatasetTag) -> None:
        pass

    @abc.abstractmethod
    def delete_tag(self, tag_id: uuid.UUID) -> None:
        pass
