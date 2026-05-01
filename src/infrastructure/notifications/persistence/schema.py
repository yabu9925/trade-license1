from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
import datetime
from src.infrastructure.database import Base

class NotificationRecord(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    message = Column(String, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
