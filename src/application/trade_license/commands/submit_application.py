from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Dict, List

from src.domain.trade_license.value_objects import (
    AttachedDocument,
    BusinessDetails,
    PaymentRecord,
)
from src.domain.trade_license.aggregate import TradeLicenseApplication
from src.application.trade_license.ports.repository import (
    ITradeLicenseApplicationRepository,
)


# ── Command ──────────────────────────────────────────────────────────────────

@dataclass
class DocumentInput:
    file_name: str
    storage_uri: str


@dataclass
class SubmitApplicationCommand:
    """UC1 — Customer submits a new trade license application."""

    applicant_id: str
    business_name: str
    business_type: str
    business_address: str
    business_capital: float
    business_activity_description: str
    documents: List[DocumentInput]
    payment_transaction_id: str
    payment_amount: float


@dataclass
class SubmitApplicationResult:
    application_id: str


# ── Handler ───────────────────────────────────────────────────────────────────

class SubmitApplicationHandler:
    """
    Orchestrates UC1: builds value objects, calls the aggregate factory,
    persists the aggregate, and returns the new ID.
    """

    def __init__(self, repository: ITradeLicenseApplicationRepository) -> None:
        self._repo = repository

    def handle(self, command: SubmitApplicationCommand) -> SubmitApplicationResult:
        b_details = BusinessDetails(
            name=command.business_name,
            type=command.business_type,
            address=command.business_address,
            capital=command.business_capital,
            activity_description=command.business_activity_description,
        )
        attachments = [
            AttachedDocument(
                document_id=str(uuid.uuid4()),
                file_name=doc.file_name,
                storage_uri=doc.storage_uri,
            )
            for doc in command.documents
        ]
        payment = PaymentRecord(
            transaction_id=command.payment_transaction_id,
            amount=command.payment_amount,
            is_settled=True,  # Payment is confirmed by the time the command is issued
        )

        application = TradeLicenseApplication.submit_new(
            applicant_id=command.applicant_id,
            business_details=b_details,
            attachments=attachments,
            payment=payment,
        )

        self._repo.save(application)

        # Domain events can be dispatched here to a message bus
        # events = application.pull_events()

        return SubmitApplicationResult(application_id=application.id)


# ── Cancel Command & Handler ──────────────────────────────────────────────────

@dataclass
class CancelApplicationCommand:
    """UC1 — Customer cancels their own pending application."""

    application_id: str
    applicant_id: str


class CancelApplicationHandler:
    def __init__(self, repository: ITradeLicenseApplicationRepository) -> None:
        self._repo = repository

    def handle(self, command: CancelApplicationCommand) -> None:
        application = self._repo.get_by_id(command.application_id)
        application.cancel(applicant_id=command.applicant_id)
        self._repo.save(application)
