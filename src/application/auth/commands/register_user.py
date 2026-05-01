from dataclasses import dataclass
from passlib.context import CryptContext

from src.domain.auth.aggregate import User
from src.domain.trade_license.exceptions import DomainException
from src.application.auth.ports.repository import IUserRepository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@dataclass
class RegisterUserCommand:
    name: str
    phone: str
    email: str
    password: str
    role: str = "Applicant"

class RegisterUserHandler:
    def __init__(self, repository: IUserRepository):
        self._repo = repository

    def handle(self, command: RegisterUserCommand) -> str:
        existing = self._repo.get_by_email(command.email)
        if existing:
            raise DomainException("User with this email already exists.")
        
        hashed = pwd_context.hash(command.password)
        user = User.create(
            name=command.name,
            phone=command.phone,
            email=command.email,
            hashed_password=hashed,
            role=command.role
        )
        self._repo.save(user)
        return user.id
