import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.workspace import (
    WorkspaceCreate, WorkspaceUpdate, WorkspaceResponse,
    MemberAdd, MemberResponse,
)
from app.services import workspace_service

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.get("", response_model=list[WorkspaceResponse])
async def list_workspaces(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await workspace_service.list_workspaces(db, current_user.id)


@router.post("", response_model=WorkspaceResponse)
async def create_workspace(
    req: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await workspace_service.create_workspace(db, current_user.id, req)


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(workspace_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ws = await workspace_service.get_workspace(db, workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    member = await workspace_service.check_workspace_access(db, workspace_id, current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this workspace")
    return ws


@router.put("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: uuid.UUID,
    req: WorkspaceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await workspace_service.check_workspace_access(db, workspace_id, current_user.id)
    if not member or member.role.value not in ("admin",):
        raise HTTPException(status_code=403, detail="Only workspace admin can update")
    try:
        return await workspace_service.update_workspace(db, workspace_id, req)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{workspace_id}")
async def delete_workspace(
    workspace_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await workspace_service.check_workspace_access(db, workspace_id, current_user.id)
    if not member or member.role.value != "admin":
        raise HTTPException(status_code=403, detail="Only workspace admin can delete")
    try:
        await workspace_service.delete_workspace(db, workspace_id)
        return {"message": "Deleted"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{workspace_id}/members", response_model=list[MemberResponse])
async def list_members(workspace_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    member = await workspace_service.check_workspace_access(db, workspace_id, current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Not a member")
    return await workspace_service.list_members(db, workspace_id)


@router.post("/{workspace_id}/members", response_model=MemberResponse)
async def add_member(
    workspace_id: uuid.UUID,
    req: MemberAdd,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await workspace_service.check_workspace_access(db, workspace_id, current_user.id)
    if not member or member.role.value != "admin":
        raise HTTPException(status_code=403, detail="Only workspace admin can add members")
    try:
        new_member = await workspace_service.add_member(db, workspace_id, req)
        from sqlalchemy import select
        from app.models.user import User as UserModel
        user = await db.execute(select(UserModel).where(UserModel.id == new_member.user_id))
        u = user.scalar_one()
        return MemberResponse(
            id=new_member.id,
            user_id=u.id,
            username=u.username,
            email=u.email,
            role=new_member.role.value,
            joined_at=new_member.joined_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{workspace_id}/members/{user_id}")
async def remove_member(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await workspace_service.check_workspace_access(db, workspace_id, current_user.id)
    if not member or member.role.value != "admin":
        raise HTTPException(status_code=403, detail="Only workspace admin can remove members")
    try:
        await workspace_service.remove_member(db, workspace_id, user_id)
        return {"message": "Removed"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
