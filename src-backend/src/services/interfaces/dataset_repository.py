import uuid, abc

from src.core.dataset import Dataset


class DatasetRepository(abc.ABC):

    @abc.abstractmethod
    def create(self, dataset: Dataset) -> None:
        pass

    @abc.abstractmethod
    def find_by_id(self, id: uuid.UUID) -> Dataset | None:
        pass

    @abc.abstractmethod
    def find_by_owner(self, owner_id: uuid.UUID) -> list[Dataset]:
        pass

    @abc.abstractmethod
    def find_all(self) -> list[Dataset]:
        pass

    @abc.abstractmethod
    def exists(self, id: uuid.UUID) -> bool:
        pass

    @abc.abstractmethod
    def update(self, id: uuid.UUID, dataset: Dataset) -> None:
        pass

    @abc.abstractmethod
    def remove(self, id: uuid.UUID) -> None:
        pass

    @abc.abstractmethod
    def remove_batch(self, ids: list[uuid.UUID]) -> list[Exception]:
        pass
