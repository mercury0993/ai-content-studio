import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.content import ContentResponse
from app.services import dashboard_service, workspace_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
async def stats(
    workspace_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await workspace_service.check_workspace_access(db, workspace_id, current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Not a member")
    data = await dashboard_service.get_stats(db, workspace_id)
    return {"code": 0, "data": data}


@router.get("/trend")
async def trend(
    workspace_id: uuid.UUID,
    days: int = Query(30, ge=7, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await workspace_service.check_workspace_access(db, workspace_id, current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Not a member")
    data = await dashboard_service.get_trend(db, workspace_id, days)
    return {"code": 0, "data": data}


@router.get("/model-usage")
async def model_usage(
    workspace_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await workspace_service.check_workspace_access(db, workspace_id, current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Not a member")
    data = await dashboard_service.get_model_usage(db, workspace_id)
    return {"code": 0, "data": data}


@router.get("/user-ranking")
async def user_ranking(
    workspace_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await workspace_service.check_workspace_access(db, workspace_id, current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Not a member")
    data = await dashboard_service.get_user_ranking(db, workspace_id)
    return {"code": 0, "data": data}


@router.get("/recent")
async def recent(
    workspace_id: uuid.UUID,
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await workspace_service.check_workspace_access(db, workspace_id, current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Not a member")
    items = await dashboard_service.get_recent(db, workspace_id, limit)
    return {"code": 0, "data": [ContentResponse.model_validate(c) for c in items]}
