from __future__ import annotations

import uuid
from typing import List, Optional

from .enums import ApplicationStatus, LicenseType, ReviewAction, ApprovalAction
from .events.domain_events import (
    DomainEvent,
    ApplicationSubmittedEvent,
    ApplicationCancelledEvent,
    ApplicationReviewedEvent,
    ApplicationApprovalProcessedEvent,
)
from .exceptions import DomainException
from .value_objects import AttachedDocument, BusinessDetails, PaymentRecord

# Statuses from which a reviewer can act
_REVIEWABLE_STATUSES = {ApplicationStatus.Pending, ApplicationStatus.Rereview}


class TradeLicenseApplication:
    """
    Aggregate Root for the Trade License bounded context.

    This is the single consistency boundary — all state transitions must
    go through this class. It enforces every business invariant and raises
    domain events for decoupled side-effects.

    Lifecycle:
        [Pending] ──Reviewer: Accept──► [Accepted] ──Approver: Approve──► [Approved]
                │                             │
           Reviewer: Reject            Approver: Reject
                │                             │
           [Rejected]                    [Rejected]
                │
           Reviewer: Adjust──► [Adjusted] (applicant resubmits → Pending)
                                      │
                               Approver: Rereview──► [Rereview] ──► (reviewer re-reviews)
    """

    def __init__(
        self,
        id: str,
        applicant_id: str,
        license_type: LicenseType,
        business_details: BusinessDetails,
        attachments: List[AttachedDocument],
        payment: PaymentRecord,
        status: ApplicationStatus = ApplicationStatus.Pending,
        reviewer_id: Optional[str] = None,
        approver_id: Optional[str] = None,
        review_note: Optional[str] = None,
        approval_note: Optional[str] = None,
    ) -> None:
        self._id = id
        self._applicant_id = applicant_id
        self._license_type = license_type
        self._business_details = business_details
        self._attachments = list(attachments)
        self._payment = payment
        self._status = status
        self._reviewer_id = reviewer_id
        self._approver_id = approver_id
        self._review_note = review_note
        self._approval_note = approval_note
        self._domain_events: List[DomainEvent] = []

    # ── Properties (read-only exposure) ────────────────────────────────────────

    @property
    def id(self) -> str:
        return self._id

    @property
    def applicant_id(self) -> str:
        return self._applicant_id

    @property
    def license_type(self) -> LicenseType:
        return self._license_type

    @property
    def status(self) -> ApplicationStatus:
        return self._status

    @property
    def business_details(self) -> BusinessDetails:
        return self._business_details

    @property
    def attachments(self) -> List[AttachedDocument]:
        return list(self._attachments)

    @property
    def payment(self) -> PaymentRecord:
        return self._payment

    @property
    def reviewer_id(self) -> Optional[str]:
        return self._reviewer_id

    @property
    def approver_id(self) -> Optional[str]:
        return self._approver_id

    @property
    def review_note(self) -> Optional[str]:
        return self._review_note

    @property
    def approval_note(self) -> Optional[str]:
        return self._approval_note

    # ── Factory: Use Case 1 — Submit New Application ───────────────────────────

    @classmethod
    def submit_new(
        cls,
        applicant_id: str,
        business_details: BusinessDetails,
        attachments: List[AttachedDocument],
        payment: PaymentRecord,
    ) -> "TradeLicenseApplication":
        """
        Creates a new application in Pending status.
        Enforces: payment must be settled, at least one attachment required.
        """
        if not payment.is_settled:
            raise DomainException("Payment must be settled before submission.")
        if not attachments:
            raise DomainException("At least one attachment is required.")

        app = cls(
            id=str(uuid.uuid4()),
            applicant_id=applicant_id,
            license_type=LicenseType.TradeLicense,
            business_details=business_details,
            attachments=attachments,
            payment=payment,
            status=ApplicationStatus.Pending,
        )
        app._add_event(ApplicationSubmittedEvent(aggregate_id=app.id))
        return app

    # ── Use Case 1 — Cancel Application ────────────────────────────────────────

    def cancel(self, applicant_id: str) -> None:
        """
        Allows the original applicant to cancel a Pending application.
        Only the owning applicant may cancel, and only while status is Pending.
        """
        if self._applicant_id != applicant_id:
            raise DomainException("Only the applicant can cancel their own application.")
        if self._status != ApplicationStatus.Pending:
            raise DomainException(
                f"Only Pending applications can be cancelled. Current status: {self._status.value}"
            )
        self._status = ApplicationStatus.Cancelled
        self._add_event(ApplicationCancelledEvent(aggregate_id=self._id))

    # ── Use Case 2 — Review Application ────────────────────────────────────────

    def review(
        self,
        reviewer_id: str,
        action: ReviewAction,
        note: Optional[str] = None,
    ) -> None:
        """
        Reviewer processes a Pending or Rereview application.
        Valid actions: Accept → Accepted | Reject → Rejected | Adjust → Adjusted
        """
        if self._status not in _REVIEWABLE_STATUSES:
            raise DomainException(
                f"Cannot review an application in status: {self._status.value}. "
                f"Expected one of: {', '.join(s.value for s in _REVIEWABLE_STATUSES)}."
            )

        self._reviewer_id = reviewer_id
        self._review_note = note

        if action == ReviewAction.Accept:
            self._status = ApplicationStatus.Accepted
        elif action == ReviewAction.Reject:
            self._status = ApplicationStatus.Rejected
        elif action == ReviewAction.Adjust:
            self._status = ApplicationStatus.Adjusted

        self._add_event(ApplicationReviewedEvent(aggregate_id=self._id, action=action.value))

    # ── Use Case 3 — Process Approval ──────────────────────────────────────────

    def process_approval(
        self,
        approver_id: str,
        action: ApprovalAction,
        note: Optional[str] = None,
    ) -> None:
        """
        Approver processes an Accepted application.
        Valid actions: Approve → Approved | Reject → Rejected | Rereview → Rereview
        """
        if self._status != ApplicationStatus.Accepted:
            raise DomainException(
                f"Only Accepted applications can be sent for approval. "
                f"Current status: {self._status.value}."
            )

        self._approver_id = approver_id
        self._approval_note = note

        if action == ApprovalAction.Approve:
            self._status = ApplicationStatus.Approved
        elif action == ApprovalAction.Reject:
            self._status = ApplicationStatus.Rejected
        elif action == ApprovalAction.Rereview:
            self._status = ApplicationStatus.Rereview

        self._add_event(
            ApplicationApprovalProcessedEvent(aggregate_id=self._id, action=action.value)
        )

    # ── Use Case 4 — Renew License ─────────────────────────────────────────────

    def create_renewal(
        self, 
        payment: PaymentRecord, 
        business_details: Optional[BusinessDetails] = None
    ) -> "TradeLicenseApplication":
        """
        Creates a new application based on this Approved one.
        Must provide a new settled payment.
        """
        if self._status != ApplicationStatus.Approved:
            raise DomainException("Only Approved licenses can be renewed.")
        
        if not payment.is_settled:
            raise DomainException("Renewal requires a new settled payment.")

        return TradeLicenseApplication.submit_new(
            applicant_id=self._applicant_id,
            business_details=business_details or self._business_details,
            attachments=self._attachments,
            payment=payment,
        )

    # ── Domain Event Helpers ────────────────────────────────────────────────────

    def _add_event(self, event: DomainEvent) -> None:
        self._domain_events.append(event)

    def pull_events(self) -> List[DomainEvent]:
        """Returns and clears all pending domain events (collect-and-clear pattern)."""
        events = list(self._domain_events)
        self._domain_events.clear()
        return events

    def __repr__(self) -> str:
        return (
            f"TradeLicenseApplication(id={self._id!r}, "
            f"status={self._status.value!r}, "
            f"applicant_id={self._applicant_id!r})"
        )
