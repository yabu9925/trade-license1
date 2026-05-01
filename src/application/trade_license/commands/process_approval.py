from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from src.domain.trade_license.enums import ApprovalAction
from src.application.trade_license.ports.repository import ITradeLicenseApplicationRepository
from src.infrastructure.notifications.repository import NotificationRepository
from sqlalchemy.orm import Session

@dataclass
class ProcessApprovalCommand:
    application_id: str
    approver_id: str
    action: ApprovalAction
    note: Optional[str] = None

class ProcessApprovalHandler:
    def __init__(self, repository: ITradeLicenseApplicationRepository, db: Session) -> None:
        self._repo = repository
        self._db = db

    def handle(self, command: ProcessApprovalCommand) -> None:
        application = self._repo.get_by_id(command.application_id)
        application.process_approval(
            approver_id=command.approver_id,
            action=command.action,
            note=command.note,
        )
        self._repo.save(application)

        # Create notification for applicant
        notif_repo = NotificationRepository(self._db)
        notif_repo.create(
            user_id=application.applicant_id,
            message=f"Your application {application.id[-6:]} has been approved decision: {command.action.value}. Note: {command.note or 'No note'}"
        )
