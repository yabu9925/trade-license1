from typing import List

from sqlalchemy.orm import Session

from src.domain.trade_license.aggregate import TradeLicenseApplication
from src.domain.trade_license.exceptions import NotFoundException
from src.domain.trade_license.value_objects import BusinessDetails, AttachedDocument, PaymentRecord
from src.application.trade_license.ports.repository import ITradeLicenseApplicationRepository
from src.infrastructure.trade_license.persistence.schema import ApplicationRecord


class SqlAlchemyTradeLicenseRepository(ITradeLicenseApplicationRepository):
    """
    SQLAlchemy implementation of the repository port.
    Maps between the SQLAlchemy ApplicationRecord and the TradeLicenseApplication Domain Aggregate.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def _to_domain(self, record: ApplicationRecord) -> TradeLicenseApplication:
        b_details = BusinessDetails(**record.business_details)
        attachments = [AttachedDocument(**a) for a in record.attachments]
        payment = PaymentRecord(**record.payment)
        
        return TradeLicenseApplication(
            id=record.id,
            applicant_id=record.applicant_id,
            license_type=record.license_type,
            business_details=b_details,
            attachments=attachments,
            payment=payment,
            status=record.status,
            reviewer_id=record.reviewer_id,
            approver_id=record.approver_id,
            review_note=record.review_note,
            approval_note=record.approval_note,
        )

    def _to_persistence(self, app: TradeLicenseApplication) -> ApplicationRecord:
        return ApplicationRecord(
            id=app.id,
            applicant_id=app.applicant_id,
            license_type=app.license_type,
            status=app.status,
            business_details={
                "name": app.business_details.name,
                "type": app.business_details.type,
                "address": app.business_details.address,
                "capital": app.business_details.capital,
                "activity_description": app.business_details.activity_description
            },
            attachments=[
                {"document_id": a.document_id, "file_name": a.file_name, "storage_uri": a.storage_uri}
                for a in app.attachments
            ],
            payment={
                "transaction_id": app.payment.transaction_id, 
                "amount": app.payment.amount, 
                "is_settled": app.payment.is_settled
            },
            reviewer_id=app.reviewer_id,
            approver_id=app.approver_id,
            review_note=app.review_note,
            approval_note=app.approval_note,
        )

    def get_by_id(self, application_id: str) -> TradeLicenseApplication:
        record = self._session.query(ApplicationRecord).filter_by(id=application_id).first()
        if not record:
            raise NotFoundException(f"Application {application_id} not found.")
        return self._to_domain(record)

    def save(self, application: TradeLicenseApplication) -> None:
        record = self._to_persistence(application)
        self._session.merge(record)
        self._session.commit()

    def find_all(self) -> List[TradeLicenseApplication]:
        records = self._session.query(ApplicationRecord).all()
        return [self._to_domain(r) for r in records]

    def find_by_applicant(self, applicant_id: str) -> List[TradeLicenseApplication]:
        records = self._session.query(ApplicationRecord).filter_by(applicant_id=applicant_id).all()
        return [self._to_domain(r) for r in records]
