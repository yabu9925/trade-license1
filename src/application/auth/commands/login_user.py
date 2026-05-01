import datetime
import jwt
from dataclasses import dataclass
from passlib.context import CryptContext

from src.domain.trade_license.exceptions import DomainException
from src.application.auth.ports.repository import IUserRepository

SECRET_KEY = "SUPER_SECRET_KEY_NEEDS_TO_BE_IN_ENV"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@dataclass
class LoginUserCommand:
    email: str
    password: str

class LoginUserHandler:
    def __init__(self, repository: IUserRepository):
        self._repo = repository

    def handle(self, command: LoginUserCommand) -> str:
        user = self._repo.get_by_email(command.email)
        print(f"DEBUG LOGIN: Searching for email '{command.email}'. Found user: {user is not None}")
        if user:
            print(f"DEBUG LOGIN: DB Hash: {user.hashed_password}, verifying...")
            is_valid = pwd_context.verify(command.password, user.hashed_password)
            print(f"DEBUG LOGIN: Verify Result: {is_valid}")
        if not user or not pwd_context.verify(command.password, user.hashed_password):
            raise DomainException("Invalid email or password.")

        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {
            "sub": user.id,
            "email": user.email,
            "role": user.role,
            "exp": expire
        }
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
