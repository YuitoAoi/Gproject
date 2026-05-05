import abc, uuid

from src.core.user import User


class UserRepository(abc.ABC):
    @abc.abstractmethod
    def create(self, user: User) -> None:
        pass

    @abc.abstractmethod
    def find_by_id(self, id: uuid.UUID) -> User | None:
        pass

    @abc.abstractmethod
    def find_by_email(self, email: str) -> User | None:
        pass

    @abc.abstractmethod
    def find_all(self) -> list[User]:
        pass

    @abc.abstractmethod
    def exists(self, id: uuid.UUID) -> bool:
        pass

    @abc.abstractmethod
    def update(self, id: uuid.UUID, user: User) -> None:
        pass

    @abc.abstractmethod
    def remove(self, id: uuid.UUID) -> None:
        pass
