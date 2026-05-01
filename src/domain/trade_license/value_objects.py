from typing import Optional
from dataclasses import dataclass

from .exceptions import DomainException


@dataclass(frozen=True)
class BusinessDetails:
    """
    Value Object — immutable, compared by value, no identity.
    Represents the full business details of the applicant.
    """

    name: str
    type: str
    address: str
    capital: Optional[float]
    activity_description: str

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise DomainException("Business name is required.")
        if not self.type or not self.type.strip():
            raise DomainException("Business type is required.")
        if not self.address or not self.address.strip():
            raise DomainException("Business address is required.")
        if not self.activity_description or not self.activity_description.strip():
            raise DomainException("Activity description is required.")


@dataclass(frozen=True)
class AttachedDocument:
    """
    Value Object — represents a document attached to the application.
    Immutable once created; identified by storageUri rather than a domain ID.
    """

    document_id: str
    file_name: str
    storage_uri: str

    def __post_init__(self) -> None:
        if not self.document_id:
            raise DomainException("Document ID is required.")
        if not self.file_name:
            raise DomainException("File name is required.")
        if not self.storage_uri:
            raise DomainException("Storage URI is required.")


@dataclass(frozen=True)
class PaymentRecord:
    """
    Value Object — records payment information for the application fee.
    Amount must be positive and the payment must be settled before submission.
    """

    transaction_id: str
    amount: float
    is_settled: bool

    def __post_init__(self) -> None:
        if self.amount <= 0:
            raise DomainException("Payment amount must be positive.")
        if not self.transaction_id:
            raise DomainException("Transaction ID is required.")
