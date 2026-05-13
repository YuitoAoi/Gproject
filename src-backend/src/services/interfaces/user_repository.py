import abc

from src.core.user import User


class UserRepository(abc.ABC):
    @abc.abstractmethod
    def create(self, user: User) -> int | None:
        pass

    @abc.abstractmethod
    def find_by_id(self, id: int) -> User | None:
        pass

    @abc.abstractmethod
    def find_by_name(self, name: str) -> User | None:
        pass

    @abc.abstractmethod
    def find_by_email(self, email: str) -> User | None:
        pass

    @abc.abstractmethod
    def find_all(self) -> list[User]:
        pass

    @abc.abstractmethod
    def exists(self, id: int) -> bool:
        pass

    @abc.abstractmethod
    def update(self, id: int, user: User) -> User | None:
        pass

    @abc.abstractmethod
    def remove(self, id: int) -> User | None:
        pass
