import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AIModelCreate(BaseModel):
    workspace_id: uuid.UUID
    name: str
    provider: str
    api_key: str | None = None
    base_url: str | None = None
    model_name: str
    default_params: dict | None = None


class AIModelUpdate(BaseModel):
    name: str | None = None
    provider: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    model_name: str | None = None
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
