import uuid
from datetime import datetime
from pydantic import BaseModel


class PromptCreate(BaseModel):
    workspace_id: uuid.UUID
    title: str
    content: str
    category: str | None = None
    tags: list[str] | None = None
    variables: list[dict] | None = None


class PromptUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    category: str | None = None
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

    class Config:
        from_attributes = True


class PromptVersionResponse(BaseModel):
    id: uuid.UUID
    prompt_id: uuid.UUID
    version: int
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
