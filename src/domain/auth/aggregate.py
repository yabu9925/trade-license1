import uuid

from src.domain.trade_license.exceptions import DomainException

class User:
    """
    Aggregate Root for User Authentication and Identity.
    """
    def __init__(
        self,
        id: str,
        name: str,
        phone: str,
        email: str,
        hashed_password: str,
        role: str
    ):
        self._id = id
        self._name = name
        self._phone = phone
        self._email = email
        self._hashed_password = hashed_password
        self._role = role

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def phone(self) -> str:
        return self._phone

    @property
    def email(self) -> str:
        return self._email

    @property
    def hashed_password(self) -> str:
        return self._hashed_password

    @property
    def role(self) -> str:
        return self._role

    @classmethod
    def create(cls, name: str, phone: str, email: str, hashed_password: str, role: str = "Applicant") -> "User":
        if not email or "@" not in email:
            raise DomainException("Invalid email format.")
        if len(hashed_password) < 10:
            raise DomainException("Hashed password must be valid.")
        
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            phone=phone,
            email=email,
            hashed_password=hashed_password,
            role=role
        )
