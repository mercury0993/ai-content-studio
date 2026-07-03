import re
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator


class RegisterRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    email: str = Field(min_length=1, max_length=100, pattern=r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
    password: str = Field(min_length=10, max_length=100)

    @field_validator("password")
    @classmethod
    def password_must_have_letters_and_digits(cls, v: str) -> str:
        if not re.search(r'[A-Za-z]', v) or not re.search(r'\d', v):
            raise ValueError("密码必须同时包含字母和数字")
        if not re.search(r'[A-Z]', v):
            raise ValueError("密码必须包含至少一个大写字母")
        if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', v):
            raise ValueError("密码必须包含至少一个特殊字符")
        return v


class LoginRequest(BaseModel):
    email: str = Field(..., max_length=100)
    password: str = Field(..., min_length=1, max_length=100)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    role: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class UpdateProfileRequest(BaseModel):
    username: str | None = Field(None, max_length=50)
    email: str | None = Field(None, max_length=100)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=10, max_length=100)

    @field_validator("new_password")
    @classmethod
    def new_password_must_have_letters_and_digits(cls, v: str) -> str:
        if not re.search(r'[A-Za-z]', v) or not re.search(r'\d', v):
            raise ValueError("密码必须同时包含字母和数字")
        if not re.search(r'[A-Z]', v):
            raise ValueError("密码必须包含至少一个大写字母")
        if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', v):
            raise ValueError("密码必须包含至少一个特殊字符")
        return v
