import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember, WorkspaceMemberRole
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate, MemberAdd


async def create_workspace(db: AsyncSession, owner_id: uuid.UUID, req: WorkspaceCreate) -> Workspace:
    workspace = Workspace(name=req.name, description=req.description, owner_id=owner_id)
    db.add(workspace)
    await db.flush()

    member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=owner_id,
        role=WorkspaceMemberRole.ADMIN,
    )
    db.add(member)
    await db.flush()
    return workspace


async def list_workspaces(db: AsyncSession, user_id: uuid.UUID) -> list[Workspace]:
    result = await db.execute(
        select(Workspace)
        .join(WorkspaceMember)
        .where(WorkspaceMember.user_id == user_id)
        .options(selectinload(Workspace.members))
    )
    return list(result.scalars().all())


async def get_workspace(db: AsyncSession, workspace_id: uuid.UUID) -> Workspace | None:
    result = await db.execute(
        select(Workspace).where(Workspace.id == workspace_id).options(selectinload(Workspace.members))
    )
    return result.scalar_one_or_none()


async def update_workspace(db: AsyncSession, workspace_id: uuid.UUID, req: WorkspaceUpdate) -> Workspace:
    workspace = await get_workspace(db, workspace_id)
    if not workspace:
        raise ValueError("Workspace not found")
    if req.name is not None:
        workspace.name = req.name
    if req.description is not None:
        workspace.description = req.description
    await db.flush()
    return workspace


async def delete_workspace(db: AsyncSession, workspace_id: uuid.UUID) -> None:
    workspace = await get_workspace(db, workspace_id)
    if not workspace:
        raise ValueError("Workspace not found")
    await db.delete(workspace)
    await db.flush()


async def add_member(db: AsyncSession, workspace_id: uuid.UUID, req: MemberAdd) -> dict:
    existing = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == req.user_id,
        )
    )
    if existing.scalar_one_or_none():
        raise ValueError("User already a member")

    user_result = await db.execute(select(User).where(User.id == req.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise ValueError("User not found")

    member = WorkspaceMember(
        workspace_id=workspace_id,
        user_id=req.user_id,
        role=WorkspaceMemberRole(req.role),
    )
    db.add(member)
    await db.flush()

    return {
        "id": member.id,
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "role": member.role.value,
        "joined_at": member.joined_at,
    }


async def remove_member(db: AsyncSession, workspace_id: uuid.UUID, user_id: uuid.UUID) -> None:
    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise ValueError("Member not found")
    await db.delete(member)
    await db.flush()


async def list_members(db: AsyncSession, workspace_id: uuid.UUID) -> list[dict]:
    result = await db.execute(
        select(WorkspaceMember, User)
        .join(User, WorkspaceMember.user_id == User.id)
        .where(WorkspaceMember.workspace_id == workspace_id)
    )
    members = []
    for member, user in result.all():
        members.append({
            "id": member.id,
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "role": member.role.value,
            "joined_at": member.joined_at,
        })
    return members


async def check_workspace_access(db: AsyncSession, workspace_id: uuid.UUID, user_id: uuid.UUID) -> WorkspaceMember | None:
    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()
