from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.trade_license.aggregate import TradeLicenseApplication


class ITradeLicenseApplicationRepository(ABC):
    """
    Repository port — defined in Application layer, implemented in Infrastructure.
    The dependency always points inward (Dependency Inversion Principle).
    """

    @abstractmethod
    def get_by_id(self, application_id: str) -> TradeLicenseApplication:
        """
        Load an aggregate by its ID.
        Raises NotFoundException if not found.
        """
        ...

    @abstractmethod
    def save(self, application: TradeLicenseApplication) -> None:
        """Persist a new or updated aggregate (upsert semantics)."""
        ...

    @abstractmethod
    def find_all(self) -> List[TradeLicenseApplication]:
        """Return all applications (used for list/query endpoints)."""
        ...

    @abstractmethod
    def find_by_applicant(self, applicant_id: str) -> List[TradeLicenseApplication]:
        """Return all applications belonging to a specific applicant."""
        ...
