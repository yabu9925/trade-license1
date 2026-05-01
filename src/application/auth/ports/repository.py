from abc import ABC, abstractmethod
from typing import Optional

from src.domain.auth.aggregate import User

class IUserRepository(ABC):
    @abstractmethod
    def save(self, user: User) -> None:
        ...

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        ...

    @abstractmethod
    def get_by_id(self, id: str) -> Optional[User]:
        ...
