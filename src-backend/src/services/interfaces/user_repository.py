from typing import List, Optional
import abc

from src.core.user import User

class UserRepository(abc.ABC):
    @abc.abstractmethod
    def create(self, user: User) -> Optional[int]:
        pass

    @abc.abstractmethod
    def find_by_id(self,id: int) -> Optional[User]:
        pass

    @abc.abstractmethod
    def find_by_name(self,name: str) -> Optional[User]:
        pass
    
    @abc.abstractmethod
    def find_by_email(self,email: str) -> Optional[User]:
        pass

    @abc.abstractmethod
    def find_all(self) -> List[User]:
        pass

    @abc.abstractmethod
    def exists(self,id: int) -> bool:
        pass

    @abc.abstractmethod
    def update(self, id: int, user: User) -> Optional[User]:
        pass

    @abc.abstractmethod
    def remove(self, id: int) -> Optional[User]:
        pass