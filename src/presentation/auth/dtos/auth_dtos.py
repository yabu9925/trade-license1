from pydantic import BaseModel, EmailStr, Field

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2)
    phone: str = Field(..., min_length=10)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: str = "Applicant"

class RegisterResponse(BaseModel):
    user_id: str
    message: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
