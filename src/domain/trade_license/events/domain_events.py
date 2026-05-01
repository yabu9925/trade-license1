from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class DomainEvent:
    """Base class for all domain events."""

    aggregate_id: str
    occurred_on: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ApplicationSubmittedEvent(DomainEvent):
    """Raised when a customer successfully submits a new trade license application."""


@dataclass
class ApplicationCancelledEvent(DomainEvent):
    """Raised when a customer cancels their pending application."""


@dataclass
class ApplicationReviewedEvent(DomainEvent):
    """Raised when a reviewer processes an application (Accept / Reject / Adjust)."""

    action: str = ""


@dataclass
class ApplicationApprovalProcessedEvent(DomainEvent):
    """Raised when an approver processes an accepted application (Approve / Reject / Rereview)."""

    action: str = ""
