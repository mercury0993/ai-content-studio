import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class WorkspaceCreate(BaseModel):
    name: str = Field(..., max_length=100)
    description: str | None = Field(None, max_length=500)


class WorkspaceUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=500)


class WorkspaceResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    owner_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MemberAdd(BaseModel):
    user_id: uuid.UUID
    role: str = "viewer"


class MemberResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    username: str
    email: str
    role: str
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)
