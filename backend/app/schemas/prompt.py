import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class PromptCreate(BaseModel):
    workspace_id: uuid.UUID
    title: str = Field(..., max_length=200)
    content: str = Field(..., max_length=10000)
    category: str | None = Field(None, max_length=100)
    tags: list[str] | None = None
    variables: list[dict] | None = None


class PromptUpdate(BaseModel):
    title: str | None = Field(None, max_length=200)
    content: str | None = Field(None, max_length=10000)
    category: str | None = Field(None, max_length=100)
    tags: list[str] | None = None
    variables: list[dict] | None = None
    is_favorite: bool | None = None


class PromptResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    title: str
    content: str
    category: str | None
    tags: list | None
    variables: list | None
    version: int
    is_favorite: bool
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PromptVersionResponse(BaseModel):
    id: uuid.UUID
    prompt_id: uuid.UUID
    version: int
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
