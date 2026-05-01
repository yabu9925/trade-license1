from __future__ import annotations

from typing import Dict, List

from src.domain.trade_license.aggregate import TradeLicenseApplication
from src.domain.trade_license.exceptions import NotFoundException
from src.application.trade_license.ports.repository import (
    ITradeLicenseApplicationRepository,
)


class InMemoryTradeLicenseRepository(ITradeLicenseApplicationRepository):
    """
    In-memory implementation of the repository port.

    Suitable for development, testing, and demos.
    Swap this for a SQLAlchemyTradeLicenseRepository in production
    without touching any domain or application code.
    """

    def __init__(self) -> None:
        self._store: Dict[str, TradeLicenseApplication] = {}

    def get_by_id(self, application_id: str) -> TradeLicenseApplication:
        app = self._store.get(application_id)
        if app is None:
            raise NotFoundException(
                f"Trade license application '{application_id}' was not found."
            )
        return app

    def save(self, application: TradeLicenseApplication) -> None:
        self._store[application.id] = application

    def find_all(self) -> List[TradeLicenseApplication]:
        return list(self._store.values())

    def find_by_applicant(self, applicant_id: str) -> List[TradeLicenseApplication]:
        return [
            app
            for app in self._store.values()
            if app.applicant_id == applicant_id
        ]
