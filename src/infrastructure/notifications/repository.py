from sqlalchemy.orm import Session
from src.infrastructure.notifications.persistence.schema import NotificationRecord
import uuid

class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: str, message: str):
        record = NotificationRecord(
            id=str(uuid.uuid4()),
            user_id=user_id,
            message=message
        )
        self.db.add(record)
        self.db.commit()

    def get_by_user(self, user_id: str):
        return self.db.query(NotificationRecord).filter(
            NotificationRecord.user_id == user_id
        ).order_by(NotificationRecord.created_at.desc()).all()
