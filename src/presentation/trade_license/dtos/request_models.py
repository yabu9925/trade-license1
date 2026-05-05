from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from src.domain.trade_license.enums import ApprovalAction, ReviewAction


# ── Shared sub-models ─────────────────────────────────────────────────────────

class DocumentRequest(BaseModel):
    file_name: str = Field(..., json_schema_extra={"example": "trade_registration.pdf"})
    storage_uri: str = Field(..., json_schema_extra={"example": "s3://bucket/path/to/file.pdf"})


# ── UC1: Submit ───────────────────────────────────────────────────────────────

class BusinessDetailsRequest(BaseModel):
    name: str = Field(..., json_schema_extra={"example": "Tech Innovators LLC"})
    type: str = Field(..., json_schema_extra={"example": "Software Development"})
    address: str = Field(..., json_schema_extra={"example": "123 Tech Park, Addis Ababa"})
    capital: Optional[float] = Field(None, json_schema_extra={"example": 50000.0})
    activity_description: str = Field(..., json_schema_extra={"example": "Custom software and IT consulting"})


class SubmitApplicationRequest(BaseModel):
    applicant_id: str = Field(..., json_schema_extra={"example": "applicant-001"})
    business_details: BusinessDetailsRequest
    documents: List[DocumentRequest] = Field(..., min_length=1)
    payment_transaction_id: str = Field(..., json_schema_extra={"example": "txn-abc-123"})
    payment_amount: float = Field(..., gt=0, json_schema_extra={"example": 500.0})


class SubmitApplicationResponse(BaseModel):
    application_id: str


# ── UC2: Review ───────────────────────────────────────────────────────────────

class ReviewApplicationRequest(BaseModel):
    reviewer_id: str = Field(..., json_schema_extra={"example": "reviewer-001"})
    action: ReviewAction = Field(..., json_schema_extra={"example": ReviewAction.Accept})
    note: Optional[str] = Field(None, json_schema_extra={"example": "All documents verified and correct."})


# ── UC3: Approve ─────────────────────────────────────────────────────────────

class ProcessApprovalRequest(BaseModel):
    approver_id: str = Field(..., json_schema_extra={"example": "approver-001"})
    action: ApprovalAction = Field(..., json_schema_extra={"example": ApprovalAction.Approve})
    note: Optional[str] = Field(None, json_schema_extra={"example": "Application meets all regulatory requirements."})


# ── Query responses ───────────────────────────────────────────────────────────

class BusinessDetailsResponse(BaseModel):
    name: str
    type: str
    address: str
    capital: Optional[float]
    activity_description: str


class AttachmentResponse(BaseModel):
    document_id: str
    file_name: str
    storage_uri: str


class PaymentResponse(BaseModel):
    transaction_id: str
    amount: float
    is_settled: bool


class ApplicationDetailResponse(BaseModel):
    id: str
    applicant_id: str
    license_type: str
    status: str
    business_details: BusinessDetailsResponse
    attachments: List[AttachmentResponse]
    payment: PaymentResponse
    reviewer_id: Optional[str]
    approver_id: Optional[str]
    review_note: Optional[str]
    approval_note: Optional[str]


class ApplicationSummaryResponse(BaseModel):
    id: str
    applicant_id: str
    status: str
    business_type: str
    payment_transaction_id: Optional[str] = None
    payment_amount: Optional[float] = None
