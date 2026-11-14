from typing import Optional
from pydantic import BaseModel, EmailStr

class FacultyLoginInitRequest(BaseModel):
    email: EmailStr
    password: str

class FacultyLoginInitResponse(BaseModel):
    status: str = "OTP_SENT"
    message: str
    session_ticket: str
    dev_otp: Optional[str] = None  # Included only in development mode for convenience

class FacultyVerifyOTPRequest(BaseModel):
    session_ticket: str
    otp_code: str

class StudentLoginRequest(BaseModel):
    identifier: str  # Roll number or Email
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    roll_number: Optional[str] = None
    full_name: str
    role: str
    department: Optional[str] = None

    model_config = {"from_attributes": True}

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    role: str
    user: UserResponse
