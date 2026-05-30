import uuid
from datetime import datetime
from pydantic import BaseModel


class ContentGenerate(BaseModel):
    workspace_id: uuid.UUID
    prompt_id: uuid.UUID
    model_id: uuid.UUID
    variables: dict | None = None


class ContentUpdate(BaseModel):
    edited_text: str | None = None


class ContentResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    prompt_id: uuid.UUID
    model_id: uuid.UUID
    variables_used: dict | None
    generated_text: str
    edited_text: str | None
    status: str
    token_usage: int
    generation_time_ms: int
    review_comment: str | None
    reviewed_by: uuid.UUID | None
    reviewed_at: datetime | None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
