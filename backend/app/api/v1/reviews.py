import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.content import ContentResponse
from app.schemas.review import ReviewSubmit, ReviewAction, BatchReview
from app.services import review_service, workspace_service, content_service

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("", response_model=dict)
async def list_reviews(
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
    items, total = await review_service.list_reviews(db, workspace_id, status, page, page_size)
    return {
        "code": 0,
        "data": {
            "items": [ContentResponse.model_validate(c) for c in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.post("/{content_id}/submit", response_model=ContentResponse)
async def submit_for_review(
    content_id: uuid.UUID,
    req: ReviewSubmit | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    content = await content_service.get_content(db, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    member = await workspace_service.check_workspace_access(db, content.workspace_id, current_user.id)
    if not member or member.role.value == "viewer":
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    reviewer_id = req.reviewer_id if req else None
    if reviewer_id:
        reviewer_member = await workspace_service.check_workspace_access(db, content.workspace_id, reviewer_id)
        if not reviewer_member or reviewer_member.role.value == "viewer":
            raise HTTPException(status_code=400, detail="Reviewer must be a workspace member with editor or admin role")

    try:
        return await review_service.submit_for_review(db, content_id, reviewer_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{content_id}/approve", response_model=ContentResponse)
async def approve(
    content_id: uuid.UUID,
    req: ReviewAction,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role.value == "viewer":
        raise HTTPException(status_code=403, detail="Viewers cannot review")
    content = await content_service.get_content(db, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    member = await workspace_service.check_workspace_access(db, content.workspace_id, current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this workspace")
    try:
        return await review_service.approve_content(db, content_id, current_user.id, req.comment)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{content_id}/reject", response_model=ContentResponse)
async def reject(
    content_id: uuid.UUID,
    req: ReviewAction,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role.value == "viewer":
        raise HTTPException(status_code=403, detail="Viewers cannot review")
    content = await content_service.get_content(db, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    member = await workspace_service.check_workspace_access(db, content.workspace_id, current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this workspace")
    try:
        return await review_service.reject_content(db, content_id, current_user.id, req.comment)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batch")
async def batch_review(
    req: BatchReview,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role.value == "viewer":
        raise HTTPException(status_code=403, detail="Viewers cannot review")
    for cid in req.content_ids:
        content = await content_service.get_content(db, cid)
        if not content:
            raise HTTPException(status_code=404, detail=f"Content {cid} not found")
        member = await workspace_service.check_workspace_access(db, content.workspace_id, current_user.id)
        if not member:
            raise HTTPException(status_code=403, detail="Not a member of one or more workspaces")
    count = await review_service.batch_review(db, req.content_ids, req.action, current_user.id, req.comment)
    return {"code": 0, "message": f"Reviewed {count} items", "data": {"count": count}}