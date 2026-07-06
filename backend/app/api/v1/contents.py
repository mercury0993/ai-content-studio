import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.content import ContentGenerate, ContentUpdate, ContentResponse
from app.services import content_service, workspace_service

router = APIRouter(prefix="/contents", tags=["contents"])

limiter = Limiter(key_func=get_remote_address)
_is_test = os.getenv("PYTEST_RUNNING", "0") == "1"


def _limit(rate: str):
    """Apply rate limit decorator; skip in test mode."""
    if _is_test:
        return lambda f: f
    return limiter.limit(rate)


@router.get("", response_model=dict)
async def list_contents(
    workspace_id: uuid.UUID,
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await workspace_service.check_workspace_access(db, workspace_id, current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Not a member")
    items, total = await content_service.list_contents(db, workspace_id, status, page, page_size)
    return {
        "code": 0,
        "data": {
            "items": [ContentResponse.model_validate(c) for c in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.post("/generate", response_model=ContentResponse)
@_limit("5/minute")
async def generate_content(
    req: ContentGenerate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await workspace_service.check_workspace_access(db, req.workspace_id, current_user.id)
    if not member or member.role.value == "viewer":
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    try:
        return await content_service.generate_content(db, current_user.id, req)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/generate-stream")
@_limit("5/minute")
async def generate_content_stream(
    req: ContentGenerate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await workspace_service.check_workspace_access(db, req.workspace_id, current_user.id)
    if not member or member.role.value == "viewer":
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    try:
        await content_service.validate_stream_request(db, req)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return StreamingResponse(
        content_service.generate_content_stream(db, current_user.id, req),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no"},
    )


@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(content_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    content = await content_service.get_content(db, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    member = await workspace_service.check_workspace_access(db, content.workspace_id, current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Not a member")
    return content


@router.put("/{content_id}", response_model=ContentResponse)
async def update_content(
    content_id: uuid.UUID,
    req: ContentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    content = await content_service.get_content(db, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    member = await workspace_service.check_workspace_access(db, content.workspace_id, current_user.id)
    if not member or member.role.value == "viewer":
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    try:
        return await content_service.update_content(db, content_id, req)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{content_id}")
async def delete_content(content_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    content = await content_service.get_content(db, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    member = await workspace_service.check_workspace_access(db, content.workspace_id, current_user.id)
    if not member or member.role.value == "viewer":
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    try:
        await content_service.delete_content(db, content_id)
        return {"message": "Deleted"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
