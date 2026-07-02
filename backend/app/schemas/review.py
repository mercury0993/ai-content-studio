import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ReviewSubmit(BaseModel):
    reviewer_id: uuid.UUID | None = None


class ReviewAction(BaseModel):
    comment: str | None = None


class BatchReview(BaseModel):
    content_ids: list[uuid.UUID]
    action: str  # "approve" or "reject"
    comment: str | None = None


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    action: str
    resource_type: str
    resource_id: uuid.UUID
    details: dict | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)