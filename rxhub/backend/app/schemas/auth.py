from pydantic import BaseModel, Field
from typing import Optional


class LoginRequest(BaseModel):
    member_id: str = Field(..., min_length=1, max_length=50)
    phone: str = Field(..., min_length=5, max_length=20)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    auth_method: str
    member_id: str
    member_name: str


class SendOTPRequest(BaseModel):
    member_id: str = Field(..., min_length=1, max_length=50)


class SendOTPResponse(BaseModel):
    message: str
    phone_masked: str


class VerifyOTPRequest(BaseModel):
    member_id: str = Field(..., min_length=1, max_length=50)
    otp: str = Field(..., min_length=4, max_length=8)


class AdminLoginRequest(BaseModel):
    email: str
    password: str


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    admin_name: str
    role: str
