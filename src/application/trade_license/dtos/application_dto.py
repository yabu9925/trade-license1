from __future__ import annotations

from typing import List, Optional
from dataclasses import dataclass

from src.domain.trade_license.enums import ApplicationStatus


@dataclass(frozen=True)
class BusinessDetailsDto:
    name: str
    type: str
    address: str
    capital: Optional[float]
    activity_description: str


@dataclass(frozen=True)
class AttachmentDto:
    document_id: str
    file_name: str
    storage_uri: str


@dataclass(frozen=True)
class PaymentDto:
    transaction_id: str
    amount: float
    is_settled: bool


@dataclass(frozen=True)
class ApplicationDetailDto:
    """Full read model — used by reviewer/approver detail view."""

    id: str
    applicant_id: str
    license_type: str
    status: ApplicationStatus
    business_details: BusinessDetailsDto
    attachments: List[AttachmentDto]
    payment: PaymentDto
    reviewer_id: Optional[str]
    approver_id: Optional[str]
    review_note: Optional[str]
    approval_note: Optional[str]


@dataclass(frozen=True)
class ApplicationSummaryDto:
    """Lightweight read model — used for list views."""

    id: str
    applicant_id: str
    status: ApplicationStatus
    business_type: str
    payment: Optional[PaymentDto] = None
