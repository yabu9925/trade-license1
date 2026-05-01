from typing import Optional
from sqlalchemy.orm import Session

from src.domain.auth.aggregate import User
from src.application.auth.ports.repository import IUserRepository
from src.infrastructure.auth.persistence.schema import UserRecord

class SqlAlchemyUserRepository(IUserRepository):
    def __init__(self, session: Session):
        self._session = session

    def _to_domain(self, record: UserRecord) -> User:
        return User(
            id=record.id,
            name=record.name,
            phone=record.phone,
            email=record.email,
            hashed_password=record.hashed_password,
            role=record.role
        )

    def save(self, user: User) -> None:
        record = UserRecord(
            id=user.id,
            name=user.name,
            phone=user.phone,
            email=user.email,
            hashed_password=user.hashed_password,
            role=user.role
        )
        self._session.merge(record)
        self._session.commit()

    def get_by_email(self, email: str) -> Optional[User]:
        record = self._session.query(UserRecord).filter_by(email=email).first()
        return self._to_domain(record) if record else None

    def get_by_id(self, id: str) -> Optional[User]:
        record = self._session.query(UserRecord).filter_by(id=id).first()
        return self._to_domain(record) if record else None
