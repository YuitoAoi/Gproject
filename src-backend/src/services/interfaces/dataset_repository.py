import abc
from datetime import datetime

from src.core.dataset import Dataset


class DatasetRepository(abc.ABC):

    @abc.abstractmethod
    def create(self, dataset: Dataset) -> Exception | None:
        pass

    @abc.abstractmethod
    def find_by_id(self, id: int) -> Dataset | None:
        pass

    @abc.abstractmethod
    def find_by_owner(self, owner_id: int) -> list[Dataset]:
        pass

    @abc.abstractmethod
    def find_all(self) -> list[Dataset]:
        pass

    @abc.abstractmethod
    def exists(self, id: int) -> bool:
        pass

    @abc.abstractmethod
    def update(self, id: int, dataset: Dataset) -> Exception | None:
        pass

    @abc.abstractmethod
    def remove(self, id: int) -> Exception | None:
        pass

    @abc.abstractmethod
    def remove_batch(self, ids: list[int]) -> list[Exception] | None:
        pass

    @abc.abstractmethod
    def count_by_owner_and_date(
        self, owner_id: int, date: "datetime", field: str
    ) -> int:
        pass

    @abc.abstractmethod
    def count_modified_today(self, owner_id: int, today: "datetime") -> int:
        pass
