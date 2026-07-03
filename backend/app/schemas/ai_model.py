import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class AIModelCreate(BaseModel):
    workspace_id: uuid.UUID
    name: str = Field(..., max_length=100)
    provider: str = Field(..., max_length=50)
    api_key: str | None = Field(None, max_length=500)
    base_url: str | None = Field(None, max_length=500)
    model_name: str = Field(..., max_length=100)
    default_params: dict | None = None


class AIModelUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    provider: str | None = Field(None, max_length=50)
    api_key: str | None = Field(None, max_length=500)
    base_url: str | None = Field(None, max_length=500)
    model_name: str | None = Field(None, max_length=100)
    default_params: dict | None = None


class AIModelResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    provider: str
    base_url: str | None
    model_name: str
    is_active: bool
    default_params: dict | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
