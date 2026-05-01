from sqlalchemy import Column, String, JSON, Enum
from src.infrastructure.database import Base
from src.domain.trade_license.enums import ApplicationStatus, LicenseType

class ApplicationRecord(Base):
    __tablename__ = "trade_license_applications"

    id = Column(String, primary_key=True)
    applicant_id = Column(String, nullable=False, index=True)
    license_type = Column(Enum(LicenseType), nullable=False)
    status = Column(Enum(ApplicationStatus), nullable=False)
    
    # Store value objects as JSON for simplicity in SQLite
    business_details = Column(JSON, nullable=False)
    attachments = Column(JSON, nullable=False)
    payment = Column(JSON, nullable=False)
    
    reviewer_id = Column(String, nullable=True)
    approver_id = Column(String, nullable=True)
    review_note = Column(String, nullable=True)
    approval_note = Column(String, nullable=True)
