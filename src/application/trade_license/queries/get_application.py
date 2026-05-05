from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from src.application.trade_license.dtos.application_dto import (
    ApplicationDetailDto,
    ApplicationSummaryDto,
    AttachmentDto,
    BusinessDetailsDto,
    PaymentDto,
)
from src.domain.trade_license.aggregate import TradeLicenseApplication
from src.application.trade_license.ports.repository import (
    ITradeLicenseApplicationRepository,
)


def _to_detail_dto(app: TradeLicenseApplication) -> ApplicationDetailDto:
    return ApplicationDetailDto(
        id=app.id,
        applicant_id=app.applicant_id,
        license_type=app.license_type.value,
        status=app.status,
        business_details=BusinessDetailsDto(
            name=app.business_details.name,
            type=app.business_details.type,
            address=app.business_details.address,
            capital=app.business_details.capital,
            activity_description=app.business_details.activity_description,
        ),
        attachments=[
            AttachmentDto(
                document_id=a.document_id,
                file_name=a.file_name,
                storage_uri=a.storage_uri,
            )
            for a in app.attachments
        ],
        payment=PaymentDto(
            transaction_id=app.payment.transaction_id,
            amount=app.payment.amount,
            is_settled=app.payment.is_settled,
        ),
        reviewer_id=app.reviewer_id,
        approver_id=app.approver_id,
        review_note=app.review_note,
        approval_note=app.approval_note,
    )


def _to_summary_dto(app: TradeLicenseApplication) -> ApplicationSummaryDto:
    return ApplicationSummaryDto(
        id=app.id,
        applicant_id=app.applicant_id,
        status=app.status,
        business_type=app.business_details.type,
        payment=PaymentDto(
            transaction_id=app.payment.transaction_id,
            amount=app.payment.amount,
            is_settled=app.payment.is_settled,
        ) if app.payment else None,
    )


# ── Queries & Handlers ────────────────────────────────────────────────────────

@dataclass
class GetApplicationByIdQuery:
    application_id: str


class GetApplicationByIdHandler:
    """Returns the full detail DTO for a single application."""

    def __init__(self, repository: ITradeLicenseApplicationRepository) -> None:
        self._repo = repository

    def handle(self, query: GetApplicationByIdQuery) -> ApplicationDetailDto:
        app = self._repo.get_by_id(query.application_id)
        return _to_detail_dto(app)


@dataclass
class ListApplicationsQuery:
    applicant_id: Optional[str] = None  # None = return all (admin/reviewer view)


class ListApplicationsHandler:
    """Returns a summary list, optionally filtered by applicant."""

    def __init__(self, repository: ITradeLicenseApplicationRepository) -> None:
        self._repo = repository

    def handle(self, query: ListApplicationsQuery) -> List[ApplicationSummaryDto]:
        if query.applicant_id:
            apps = self._repo.find_by_applicant(query.applicant_id)
        else:
            apps = self._repo.find_all()
        return [_to_summary_dto(a) for a in apps]
