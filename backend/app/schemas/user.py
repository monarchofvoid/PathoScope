from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    ICT_ADMIN = "ict_admin"
    ICT_MEMBER = "ict_member"
    VIEWER = "viewer"


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    role: UserRole = UserRole.ICT_MEMBER
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=12, max_length=128)

    @validator('password')
    def validate_password(cls, v):
        from ..core.security import PasswordValidator
        errors = PasswordValidator.validate(v)
        if errors:
            raise ValueError('; '.join(errors))
        return v


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: str
    created_at: datetime
    last_login: Optional[datetime]
    failed_login_attempts: int
    locked_until: Optional[datetime]
    mfa_enabled: bool

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False


class UserLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=12, max_length=128)

    @validator('new_password')
    def validate_new_password(cls, v):
        from ..core.security import PasswordValidator
        errors = PasswordValidator.validate(v)
        if errors:
            raise ValueError('; '.join(errors))
        return v


class MFADisplay(BaseModel):
    secret: str
    qr_code: str
    backup_codes: list[str]


class MFAVerify(BaseModel):
    token: str = Field(..., min_length=6, max_length=6)


class MFASetup(BaseModel):
    token: str = Field(..., min_length=6, max_length=6)
    secret: str


class UserStats(BaseModel):
    total_cases_verified: int
    tokens_generated: int
    last_login: Optional[datetime]
    account_age_days: int