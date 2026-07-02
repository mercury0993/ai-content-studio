import uuid
from pydantic import BaseModel, ConfigDict, Field


class RegisterRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    email: str = Field(min_length=1, max_length=100, pattern=r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
    password: str = Field(min_length=8, max_length=100)


class LoginRequest(BaseModel):
    email: str
    password: str


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
    username: str | None = None
    email: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
