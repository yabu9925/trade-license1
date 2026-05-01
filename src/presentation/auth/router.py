from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.infrastructure.database import get_db
from src.infrastructure.auth.sqlalchemy_repository import SqlAlchemyUserRepository
from src.application.auth.commands.register_user import RegisterUserCommand, RegisterUserHandler
from src.application.auth.commands.login_user import LoginUserCommand, LoginUserHandler
from src.domain.trade_license.exceptions import DomainException
from src.presentation.auth.dtos.auth_dtos import RegisterRequest, RegisterResponse, TokenResponse

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

def _get_repo(db: Session = Depends(get_db)) -> SqlAlchemyUserRepository:
    return SqlAlchemyUserRepository(db)

def _register_handler(repo = Depends(_get_repo)) -> RegisterUserHandler:
    return RegisterUserHandler(repo)

def _login_handler(repo = Depends(_get_repo)) -> LoginUserHandler:
    return LoginUserHandler(repo)

@router.post("/register", response_model=RegisterResponse)
def register(
    body: RegisterRequest,
    handler: RegisterUserHandler = Depends(_register_handler)
):
    try:
        user_id = handler.handle(
            RegisterUserCommand(
                name=body.name,
                phone=body.phone,
                email=body.email,
                password=body.password,
                role=body.role
            )
        )
        return RegisterResponse(user_id=user_id, message="Registration successful.")
    except DomainException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/token", response_model=TokenResponse)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    handler: LoginUserHandler = Depends(_login_handler)
):
    try:
        token = handler.handle(
            LoginUserCommand(
                email=form_data.username,  # OAuth2 uses 'username' field for email here
                password=form_data.password
            )
        )
        return TokenResponse(access_token=token, token_type="bearer")
    except DomainException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
