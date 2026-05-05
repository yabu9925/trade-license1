from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from fastapi.responses import StreamingResponse
import shutil
import os
import uuid
import io
from src.infrastructure.pdf_service import PDFService
from starlette import status as http_status
from sqlalchemy.orm import Session

from src.infrastructure.database import get_db
from src.infrastructure.trade_license.sqlalchemy_repository import SqlAlchemyTradeLicenseRepository

from src.infrastructure.notifications.repository import NotificationRepository
from src.domain.trade_license.value_objects import BusinessDetails, PaymentRecord, AttachedDocument
from src.application.trade_license.commands.submit_application import (
    CancelApplicationCommand,
    CancelApplicationHandler,
    DocumentInput,
    SubmitApplicationCommand,
    SubmitApplicationHandler,
)
from src.application.trade_license.commands.review_application import (
    ReviewApplicationCommand,
    ReviewApplicationHandler,
)
from src.application.trade_license.commands.process_approval import (
    ProcessApprovalCommand,
    ProcessApprovalHandler,
)
from src.application.trade_license.queries.get_application import (
    GetApplicationByIdHandler,
    GetApplicationByIdQuery,
    ListApplicationsHandler,
    ListApplicationsQuery,
)
from src.domain.trade_license.exceptions import DomainException, NotFoundException
from src.presentation.trade_license.dtos.request_models import (
    ApplicationDetailResponse,
    ApplicationSummaryResponse,
    AttachmentResponse,
    BusinessDetailsResponse,
    PaymentResponse,
    ProcessApprovalRequest,
    ReviewApplicationRequest,
    SubmitApplicationRequest,
    SubmitApplicationResponse,
)

router = APIRouter(prefix="/api/v1/trade-licenses", tags=["Trade Licenses"])
UPLOAD_DIR = "uploads"


# ── Dependency injection helpers ──────────────────────────────────────────────
# In a real app these would be resolved via a DI container (e.g. dependency-injector).
# Here we import a shared singleton repository from main.py via a module-level reference.

def _get_repo(db: Session = Depends(get_db)):
    return SqlAlchemyTradeLicenseRepository(db)


def _submit_handler(repo=Depends(_get_repo)) -> SubmitApplicationHandler:
    return SubmitApplicationHandler(repo)

def _cancel_handler(repo=Depends(_get_repo)) -> CancelApplicationHandler:
    return CancelApplicationHandler(repo)

def _review_handler(db: Session = Depends(get_db)) -> ReviewApplicationHandler:
    repo = SqlAlchemyTradeLicenseRepository(db)
    return ReviewApplicationHandler(repo, db)

def _approval_handler(db: Session = Depends(get_db)) -> ProcessApprovalHandler:
    repo = SqlAlchemyTradeLicenseRepository(db)
    return ProcessApprovalHandler(repo, db)

def _get_by_id_handler(repo=Depends(_get_repo)) -> GetApplicationByIdHandler:
    return GetApplicationByIdHandler(repo)

def _list_handler(repo=Depends(_get_repo)) -> ListApplicationsHandler:
    return ListApplicationsHandler(repo)


# ── Endpoint helpers ──────────────────────────────────────────────────────────

def _handle_errors(exc: Exception) -> None:
    if isinstance(exc, NotFoundException):
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, DomainException):
        raise HTTPException(status_code=http_status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc))
    raise exc


# ── POST /api/v1/trade-licenses ───────────────────────────────────────────────

@router.post(
    "",
    response_model=SubmitApplicationResponse,
    status_code=http_status.HTTP_201_CREATED,
    summary="UC1 — Submit a new trade license application",
)
def submit_application(
    body: SubmitApplicationRequest,
    handler: SubmitApplicationHandler = Depends(_submit_handler),
) -> SubmitApplicationResponse:
    try:
        result = handler.handle(
            SubmitApplicationCommand(
                applicant_id=body.applicant_id,
                business_name=body.business_details.name,
                business_type=body.business_details.type,
                business_address=body.business_details.address,
                business_capital=body.business_details.capital,
                business_activity_description=body.business_details.activity_description,
                documents=[DocumentInput(d.file_name, d.storage_uri) for d in body.documents],
                payment_transaction_id=body.payment_transaction_id,
                payment_amount=body.payment_amount,
            )
        )
        return SubmitApplicationResponse(application_id=result.application_id)
    except Exception as exc:
        _handle_errors(exc)


# ── POST /api/v1/trade-licenses/upload ───────────────────────────────────────

@router.post(
    "/upload",
    status_code=http_status.HTTP_201_CREATED,
    summary="Upload a document for an application",
)
async def upload_file(file: UploadFile = File(...)) -> dict:
    try:
        file_id = str(uuid.uuid4())
        extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{file_id}{extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return {
            "file_name": file.filename,
            "storage_uri": file_path
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(exc)}")


# ── DELETE /api/v1/trade-licenses/{id} ───────────────────────────────────────

@router.delete(
    "/{application_id}",
    status_code=http_status.HTTP_204_NO_CONTENT,
    summary="UC1 — Cancel a pending application (applicant only)",
)
def cancel_application(
    application_id: str,
    applicant_id: str,
    handler: CancelApplicationHandler = Depends(_cancel_handler),
) -> None:
    try:
        handler.handle(CancelApplicationCommand(application_id=application_id, applicant_id=applicant_id))
    except Exception as exc:
        _handle_errors(exc)


# ── GET /api/v1/trade-licenses ────────────────────────────────────────────────

@router.get(
    "",
    response_model=List[ApplicationSummaryResponse],
    summary="List all applications (optionally filter by applicant)",
)
def list_applications(
    applicant_id: Optional[str] = None,
    handler: ListApplicationsHandler = Depends(_list_handler),
) -> List[ApplicationSummaryResponse]:
    results = handler.handle(ListApplicationsQuery(applicant_id=applicant_id))
    return [
        ApplicationSummaryResponse(
            id=r.id,
            applicant_id=r.applicant_id,
            status=r.status.value,
            business_type=r.business_type,
            payment_transaction_id=r.payment.transaction_id if r.payment else None,
            payment_amount=r.payment.amount if r.payment else None,
        )
        for r in results
    ]


# ── GET /api/v1/notifications ────────────────────────────────────────────────

@router.get(
    "/notifications",
    summary="Get notifications for a user",
)
def get_notifications(
    user_id: str,
    db: Session = Depends(get_db),
) -> List[dict]:
    repo = NotificationRepository(db)
    notifications = repo.get_by_user(user_id)
    return [
        {
            "id": n.id,
            "message": n.message,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat()
        }
        for n in notifications
    ]


# ── GET /api/v1/trade-licenses/{id} ──────────────────────────────────────────

@router.get(
    "/{application_id}",
    response_model=ApplicationDetailResponse,
    summary="Get full application details (reviewer / approver view)",
)
def get_application(
    application_id: str,
    handler: GetApplicationByIdHandler = Depends(_get_by_id_handler),
) -> ApplicationDetailResponse:
    try:
        dto = handler.handle(GetApplicationByIdQuery(application_id=application_id))
        return ApplicationDetailResponse(
            id=dto.id,
            applicant_id=dto.applicant_id,
            license_type=dto.license_type,
            status=dto.status.value,
            business_details=BusinessDetailsResponse(
                name=dto.business_details.name,
                type=dto.business_details.type,
                address=dto.business_details.address,
                capital=dto.business_details.capital,
                activity_description=dto.business_details.activity_description
            ),
            attachments=[
                AttachmentResponse(document_id=a.document_id, file_name=a.file_name, storage_uri=a.storage_uri)
                for a in dto.attachments
            ],
            payment=PaymentResponse(
                transaction_id=dto.payment.transaction_id,
                amount=dto.payment.amount,
                is_settled=dto.payment.is_settled,
            ),
            reviewer_id=dto.reviewer_id,
            approver_id=dto.approver_id,
            review_note=dto.review_note,
            approval_note=dto.approval_note,
        )
    except Exception as exc:
        _handle_errors(exc)


# ── POST /api/v1/trade-licenses/{id}/review ───────────────────────────────────

@router.post(
    "/{application_id}/review",
    status_code=http_status.HTTP_200_OK,
    summary="UC2 — Reviewer submits Accept / Reject / Adjust decision",
)
def review_application(
    application_id: str,
    body: ReviewApplicationRequest,
    handler: ReviewApplicationHandler = Depends(_review_handler),
) -> dict:
    try:
        handler.handle(
            ReviewApplicationCommand(
                application_id=application_id,
                reviewer_id=body.reviewer_id,
                action=body.action,
                note=body.note,
            )
        )
        return {"message": "Review submitted successfully."}
    except Exception as exc:
        _handle_errors(exc)


# ── POST /api/v1/trade-licenses/{id}/approval ────────────────────────────────

@router.post(
    "/{application_id}/approval",
    status_code=http_status.HTTP_200_OK,
    summary="UC3 — Approver submits Approve / Reject / Rereview decision",
)
def process_approval(
    application_id: str,
    body: ProcessApprovalRequest,
    handler: ProcessApprovalHandler = Depends(_approval_handler),
) -> dict:
    try:
        handler.handle(
            ProcessApprovalCommand(
                application_id=application_id,
                approver_id=body.approver_id,
                action=body.action,
                note=body.note,
            )
        )
        return {"message": "Approval decision processed successfully."}
    except Exception as exc:
        _handle_errors(exc)


# ── POST /api/v1/trade-licenses/{id}/renew ───────────────────────────────────

@router.post(
    "/{application_id}/renew",
    status_code=http_status.HTTP_201_CREATED,
    summary="Renew an existing approved license",
)
def renew_license(
    application_id: str,
    body: SubmitApplicationRequest,
    repo: SqlAlchemyTradeLicenseRepository = Depends(_get_repo),
) -> SubmitApplicationResponse:
    try:
        existing_app = repo.get_by_id(application_id)
        if not existing_app:
            raise NotFoundException(f"Application {application_id} not found.")
        
        # In a real app, we'd use a handler. Here we do it inline for speed.
        new_payment = PaymentRecord(
            transaction_id=body.payment_transaction_id,
            amount=body.payment_amount,
            is_settled=True
        )
        new_biz = BusinessDetails(
            name=body.business_details.name,
            type=body.business_details.type,
            address=body.business_details.address,
            capital=body.business_details.capital,
            activity_description=body.business_details.activity_description
        )
        
        new_app = existing_app.create_renewal(
            payment=new_payment,
            business_details=new_biz
        )
        
        repo.save(new_app)
        return SubmitApplicationResponse(application_id=new_app.id)
    except Exception as exc:
        _handle_errors(exc)


# ── GET /api/v1/trade-licenses/{id}/pdf ──────────────────────────────────────

@router.get(
    "/{application_id}/pdf",
    summary="Download the approved trade license as a PDF",
)
def download_license_pdf(
    application_id: str,
    repo: SqlAlchemyTradeLicenseRepository = Depends(_get_repo),
) -> StreamingResponse:
    try:
        app = repo.get_by_id(application_id)
        if not app:
            raise NotFoundException(f"Application {application_id} not found.")
        
        if app.status.value != "Approved":
            raise DomainException("License can only be downloaded after approval.")
        
        pdf_service = PDFService()
        pdf_bytes = pdf_service.generate_license_pdf(app)
        
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=trade_license_{application_id}.pdf"}
        )
    except Exception as exc:
        _handle_errors(exc)
