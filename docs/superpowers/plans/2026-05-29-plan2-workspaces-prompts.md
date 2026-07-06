# AI Content Studio — Plan 2: Workspace + Prompt Management

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add workspace management (CRUD + members) and prompt template management (CRUD + versions + search/filter) with full backend API and frontend pages.

**Architecture:** Workspaces isolate data per team. Each workspace has its own prompts, models, contents, and members. Prompts support `{{variable}}` placeholders and version history.

**Tech Stack:** Same as Plan 1 — FastAPI, SQLAlchemy 2.0 async, Vue 3, Element Plus, Pinia

**Prerequisite:** Plan 1 completed (auth system working, Docker Compose running)

---

## Task 1: Workspace Backend — Model + Schema + Service + API

**Files:**
- Create: `backend/app/models/workspace.py`
- Create: `backend/app/schemas/workspace.py`
- Create: `backend/app/services/workspace_service.py`
- Create: `backend/app/api/v1/workspaces.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Create Workspace models**

`backend/app/models/workspace.py`:
```python
import enum
import uuid

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class WorkspaceMemberRole(str, enum.Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", foreign_keys=[owner_id])
    members = relationship("WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan")


class WorkspaceMember(Base):
    __tablename__ = "workspace_members"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role: Mapped[WorkspaceMemberRole] = mapped_column(Enum(WorkspaceMemberRole), default=WorkspaceMemberRole.VIEWER, nullable=False)
    joined_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    workspace = relationship("Workspace", back_populates="members")
    user = relationship("User")
```

- [ ] **Step 2: Update models/__init__.py**

```python
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember

__all__ = ["User", "Workspace", "WorkspaceMember"]
```

- [ ] **Step 3: Create workspace schemas**

`backend/app/schemas/workspace.py`:
```python
import uuid
from datetime import datetime
from pydantic import BaseModel


class WorkspaceCreate(BaseModel):
    name: str
    description: str | None = None


class WorkspaceUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class WorkspaceResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    owner_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


class MemberAdd(BaseModel):
    user_id: uuid.UUID
    role: str = "viewer"


class MemberResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    username: str
    email: str
    role: str
    joined_at: datetime

    class Config:
        from_attributes = True
```

- [ ] **Step 4: Create workspace service**

`backend/app/services/workspace_service.py`:
```python
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

    # Owner auto-joins as admin
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


async def add_member(db: AsyncSession, workspace_id: uuid.UUID, req: MemberAdd) -> WorkspaceMember:
    existing = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == req.user_id,
        )
    )
    if existing.scalar_one_or_none():
        raise ValueError("User already a member")

    # Verify user exists
    user = await db.execute(select(User).where(User.id == req.user_id))
    if not user.scalar_one_or_none():
        raise ValueError("User not found")

    member = WorkspaceMember(
        workspace_id=workspace_id,
        user_id=req.user_id,
        role=WorkspaceMemberRole(req.role),
    )
    db.add(member)
    await db.flush()
    return member


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
```

- [ ] **Step 5: Create workspace router**

`backend/app/api/v1/workspaces.py`:
```python
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
        # Fetch user info for response
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
```

- [ ] **Step 6: Register router in main.py**

Add to `backend/app/main.py`:
```python
from app.api.v1.workspaces import router as workspaces_router
# ... after auth_router
app.include_router(workspaces_router, prefix="/api/v1")
```

- [ ] **Step 7: Generate migration and restart**

```bash
cd E:/lx/projects/ai-content-studio/backend
alembic revision --autogenerate -m "add workspaces and workspace_members tables"
docker compose restart backend
```

- [ ] **Step 8: Commit**

```bash
git add backend/
git commit -m "feat: workspace management — CRUD + member management"
```

---

## Task 2: Prompt Backend — Model + Schema + Service + API

**Files:**
- Create: `backend/app/models/prompt.py`
- Create: `backend/app/schemas/prompt.py`
- Create: `backend/app/services/prompt_service.py`
- Create: `backend/app/api/v1/prompts.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Create Prompt models**

`backend/app/models/prompt.py`:
```python
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Prompt(Base):
    __tablename__ = "prompts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tags: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    variables: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    workspace = relationship("Workspace")
    creator = relationship("User", foreign_keys=[created_by])
    versions = relationship("PromptVersion", back_populates="prompt", cascade="all, delete-orphan")


class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prompt_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("prompts.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    prompt = relationship("Prompt", back_populates="versions")
```

- [ ] **Step 2: Update models/__init__.py**

```python
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.models.prompt import Prompt, PromptVersion

__all__ = ["User", "Workspace", "WorkspaceMember", "Prompt", "PromptVersion"]
```

- [ ] **Step 3: Create prompt schemas**

`backend/app/schemas/prompt.py`:
```python
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
```

- [ ] **Step 4: Create prompt service**

`backend/app/services/prompt_service.py`:
```python
import re
import uuid

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prompt import Prompt, PromptVersion
from app.schemas.prompt import PromptCreate, PromptUpdate


def extract_variables(content: str) -> list[dict]:
    """Extract {{variable}} placeholders from content."""
    matches = re.findall(r'\{\{(\w+)\}\}', content)
    return [{"name": m, "required": True} for m in sorted(set(matches))]


async def create_prompt(db: AsyncSession, user_id: uuid.UUID, req: PromptCreate) -> Prompt:
    variables = req.variables or extract_variables(req.content)
    prompt = Prompt(
        workspace_id=req.workspace_id,
        title=req.title,
        content=req.content,
        category=req.category,
        tags=req.tags,
        variables=variables,
        version=1,
        created_by=user_id,
    )
    db.add(prompt)
    await db.flush()

    # Save initial version
    version = PromptVersion(prompt_id=prompt.id, version=1, content=req.content)
    db.add(version)
    await db.flush()
    return prompt


async def list_prompts(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    category: str | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Prompt], int]:
    query = select(Prompt).where(Prompt.workspace_id == workspace_id)

    if category:
        query = query.where(Prompt.category == category)
    if search:
        query = query.where(or_(Prompt.title.ilike(f"%{search}%"), Prompt.content.ilike(f"%{search}%")))

    # Count
    from sqlalchemy import func
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    # Paginate
    query = query.order_by(Prompt.is_favorite.desc(), Prompt.updated_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return list(result.scalars().all()), total


async def get_prompt(db: AsyncSession, prompt_id: uuid.UUID) -> Prompt | None:
    result = await db.execute(select(Prompt).where(Prompt.id == prompt_id))
    return result.scalar_one_or_none()


async def update_prompt(db: AsyncSession, prompt_id: uuid.UUID, req: PromptUpdate) -> Prompt:
    prompt = await get_prompt(db, prompt_id)
    if not prompt:
        raise ValueError("Prompt not found")

    content_changed = req.content is not None and req.content != prompt.content

    if req.title is not None:
        prompt.title = req.title
    if req.content is not None:
        prompt.content = req.content
        prompt.variables = extract_variables(req.content)
    if req.category is not None:
        prompt.category = req.category
    if req.tags is not None:
        prompt.tags = req.tags
    if req.variables is not None:
        prompt.variables = req.variables
    if req.is_favorite is not None:
        prompt.is_favorite = req.is_favorite

    if content_changed:
        prompt.version += 1
        version = PromptVersion(prompt_id=prompt.id, version=prompt.version, content=req.content)
        db.add(version)

    await db.flush()
    return prompt


async def delete_prompt(db: AsyncSession, prompt_id: uuid.UUID) -> None:
    prompt = await get_prompt(db, prompt_id)
    if not prompt:
        raise ValueError("Prompt not found")
    await db.delete(prompt)
    await db.flush()


async def list_versions(db: AsyncSession, prompt_id: uuid.UUID) -> list[PromptVersion]:
    result = await db.execute(
        select(PromptVersion)
        .where(PromptVersion.prompt_id == prompt_id)
        .order_by(PromptVersion.version.desc())
    )
    return list(result.scalars().all())


async def rollback_version(db: AsyncSession, prompt_id: uuid.UUID, version: int) -> Prompt:
    prompt = await get_prompt(db, prompt_id)
    if not prompt:
        raise ValueError("Prompt not found")

    result = await db.execute(
        select(PromptVersion).where(
            PromptVersion.prompt_id == prompt_id,
            PromptVersion.version == version,
        )
    )
    pv = result.scalar_one_or_none()
    if not pv:
        raise ValueError("Version not found")

    prompt.content = pv.content
    prompt.version += 1
    prompt.variables = extract_variables(pv.content)

    new_version = PromptVersion(prompt_id=prompt.id, version=prompt.version, content=pv.content)
    db.add(new_version)
    await db.flush()
    return prompt
```

- [ ] **Step 5: Create prompt router**

`backend/app/api/v1/prompts.py`:
```python
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.prompt import PromptCreate, PromptUpdate, PromptResponse, PromptVersionResponse
from app.services import prompt_service, workspace_service

router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.get("", response_model=dict)
async def list_prompts(
    workspace_id: uuid.UUID,
    category: str | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await workspace_service.check_workspace_access(db, workspace_id, current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this workspace")

    items, total = await prompt_service.list_prompts(db, workspace_id, category, search, page, page_size)
    return {
        "code": 0,
        "data": {
            "items": [PromptResponse.model_validate(p) for p in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.post("", response_model=PromptResponse)
async def create_prompt(
    req: PromptCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await workspace_service.check_workspace_access(db, req.workspace_id, current_user.id)
    if not member or member.role.value == "viewer":
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return await prompt_service.create_prompt(db, current_user.id, req)


@router.get("/{prompt_id}", response_model=PromptResponse)
async def get_prompt(prompt_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    prompt = await prompt_service.get_prompt(db, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    member = await workspace_service.check_workspace_access(db, prompt.workspace_id, current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Not a member")
    return prompt


@router.put("/{prompt_id}", response_model=PromptResponse)
async def update_prompt(
    prompt_id: uuid.UUID,
    req: PromptUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    prompt = await prompt_service.get_prompt(db, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    member = await workspace_service.check_workspace_access(db, prompt.workspace_id, current_user.id)
    if not member or member.role.value == "viewer":
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    try:
        return await prompt_service.update_prompt(db, prompt_id, req)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{prompt_id}")
async def delete_prompt(prompt_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    prompt = await prompt_service.get_prompt(db, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    member = await workspace_service.check_workspace_access(db, prompt.workspace_id, current_user.id)
    if not member or member.role.value == "viewer":
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    try:
        await prompt_service.delete_prompt(db, prompt_id)
        return {"message": "Deleted"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{prompt_id}/versions", response_model=list[PromptVersionResponse])
async def list_versions(prompt_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    prompt = await prompt_service.get_prompt(db, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return await prompt_service.list_versions(db, prompt_id)


@router.post("/{prompt_id}/rollback/{version}", response_model=PromptResponse)
async def rollback_version(
    prompt_id: uuid.UUID,
    version: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    prompt = await prompt_service.get_prompt(db, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    member = await workspace_service.check_workspace_access(db, prompt.workspace_id, current_user.id)
    if not member or member.role.value == "viewer":
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    try:
        return await prompt_service.rollback_version(db, prompt_id, version)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

- [ ] **Step 6: Register router in main.py**

```python
from app.api.v1.prompts import router as prompts_router
app.include_router(prompts_router, prefix="/api/v1")
```

- [ ] **Step 7: Generate migration and restart**

```bash
cd E:/lx/projects/ai-content-studio/backend
alembic revision --autogenerate -m "add prompts and prompt_versions tables"
docker compose restart backend
```

- [ ] **Step 8: Commit**

```bash
git add backend/
git commit -m "feat: prompt management — CRUD, versions, search/filter"
```

---

## Task 3: Frontend — Workspace Pages

**Files:**
- Create: `frontend/src/api/workspaces.ts`
- Create: `frontend/src/stores/workspace.ts`
- Create: `frontend/src/views/workspaces/WorkspaceList.vue`
- Create: `frontend/src/views/workspaces/WorkspaceDetail.vue`
- Modify: `frontend/src/router/index.ts`
- Modify: `frontend/src/layouts/MainLayout.vue`

- [ ] **Step 1: Create workspace API**

`frontend/src/api/workspaces.ts`:
```typescript
import request from './request'

export function listWorkspaces() {
  return request.get('/workspaces')
}

export function createWorkspace(data: { name: string; description?: string }) {
  return request.post('/workspaces', data)
}

export function getWorkspace(id: string) {
  return request.get(`/workspaces/${id}`)
}

export function updateWorkspace(id: string, data: { name?: string; description?: string }) {
  return request.put(`/workspaces/${id}`, data)
}

export function deleteWorkspace(id: string) {
  return request.delete(`/workspaces/${id}`)
}

export function listMembers(workspaceId: string) {
  return request.get(`/workspaces/${workspaceId}/members`)
}

export function addMember(workspaceId: string, data: { user_id: string; role: string }) {
  return request.post(`/workspaces/${workspaceId}/members`, data)
}

export function removeMember(workspaceId: string, userId: string) {
  return request.delete(`/workspaces/${workspaceId}/members/${userId}`)
}
```

- [ ] **Step 2: Create workspace store**

`frontend/src/stores/workspace.ts`:
```typescript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { listWorkspaces, getWorkspace } from '@/api/workspaces'

export interface Workspace {
  id: string
  name: string
  description: string | null
  owner_id: string
  created_at: string
}

export const useWorkspaceStore = defineStore('workspace', () => {
  const workspaces = ref<Workspace[]>([])
  const currentWorkspace = ref<Workspace | null>(null)

  async function fetchWorkspaces() {
    const data: any = await listWorkspaces()
    workspaces.value = data
    if (!currentWorkspace.value && data.length > 0) {
      currentWorkspace.value = data[0]
    }
  }

  async function switchWorkspace(id: string) {
    const data: any = await getWorkspace(id)
    currentWorkspace.value = data
  }

  return { workspaces, currentWorkspace, fetchWorkspaces, switchWorkspace }
})
```

- [ ] **Step 3: Create WorkspaceList.vue**

`frontend/src/views/workspaces/WorkspaceList.vue`:
```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkspaceStore } from '@/stores/workspace'
import { createWorkspace, deleteWorkspace } from '@/api/workspaces'
import { ElMessage, ElMessageBox } from 'element-plus'

const workspaceStore = useWorkspaceStore()
const router = useRouter()
const showCreate = ref(false)
const form = ref({ name: '', description: '' })
const loading = ref(false)

onMounted(() => {
  workspaceStore.fetchWorkspaces()
})

async function handleCreate() {
  if (!form.value.name) {
    ElMessage.warning('请输入空间名称')
    return
  }
  loading.value = true
  try {
    await createWorkspace(form.value)
    ElMessage.success('创建成功')
    showCreate.value = false
    form.value = { name: '', description: '' }
    await workspaceStore.fetchWorkspaces()
  } finally {
    loading.value = false
  }
}

async function handleDelete(id: string, name: string) {
  await ElMessageBox.confirm(`确定删除空间「${name}」？`, '提示', { type: 'warning' })
  await deleteWorkspace(id)
  ElMessage.success('已删除')
  await workspaceStore.fetchWorkspaces()
}

function goDetail(id: string) {
  router.push(`/workspaces/${id}`)
}
</script>

<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
      <h3>工作空间</h3>
      <el-button type="primary" @click="showCreate = true">新建空间</el-button>
    </div>

    <el-row :gutter="16">
      <el-col :span="8" v-for="ws in workspaceStore.workspaces" :key="ws.id">
        <el-card style="margin-bottom: 16px; cursor: pointer;" @click="goDetail(ws.id)">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span style="font-weight: bold;">{{ ws.name }}</span>
              <el-button size="small" type="danger" @click.stop="handleDelete(ws.id, ws.name)">删除</el-button>
            </div>
          </template>
          <p>{{ ws.description || '暂无描述' }}</p>
          <p style="color: #999; font-size: 12px;">创建于 {{ new Date(ws.created_at).toLocaleDateString() }}</p>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="showCreate" title="新建工作空间">
      <el-form>
        <el-form-item label="名称">
          <el-input v-model="form.name" placeholder="空间名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" placeholder="空间描述（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" :loading="loading" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>
```

- [ ] **Step 4: Create WorkspaceDetail.vue**

`frontend/src/views/workspaces/WorkspaceDetail.vue`:
```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getWorkspace, listMembers, addMember, removeMember } from '@/api/workspaces'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const workspace = ref<any>(null)
const members = ref<any[]>([])
const showAddMember = ref(false)
const newMember = ref({ user_id: '', role: 'viewer' })

onMounted(async () => {
  const id = route.params.id as string
  workspace.value = await getWorkspace(id)
  members.value = await listMembers(id)
})

async function handleAddMember() {
  if (!newMember.value.user_id) {
    ElMessage.warning('请输入用户 ID')
    return
  }
  try {
    await addMember(route.params.id as string, newMember.value)
    ElMessage.success('添加成功')
    showAddMember.value = false
    members.value = await listMembers(route.params.id as string)
  } catch {
    // handled by interceptor
  }
}

async function handleRemoveMember(userId: string) {
  await ElMessageBox.confirm('确定移除该成员？', '提示', { type: 'warning' })
  await removeMember(route.params.id as string, userId)
  ElMessage.success('已移除')
  members.value = await listMembers(route.params.id as string)
}
</script>

<template>
  <div v-if="workspace">
    <h3>{{ workspace.name }}</h3>
    <p>{{ workspace.description || '暂无描述' }}</p>

    <div style="display: flex; justify-content: space-between; align-items: center; margin: 24px 0 16px;">
      <h4>成员管理</h4>
      <el-button type="primary" size="small" @click="showAddMember = true">添加成员</el-button>
    </div>

    <el-table :data="members" style="width: 100%">
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="email" label="邮箱" />
      <el-table-column prop="role" label="角色" />
      <el-table-column label="操作" width="100">
        <template #default="{ row }">
          <el-button size="small" type="danger" @click="handleRemoveMember(row.user_id)">移除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showAddMember" title="添加成员">
      <el-form>
        <el-form-item label="用户 ID">
          <el-input v-model="newMember.user_id" placeholder="输入用户 UUID" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="newMember.role">
            <el-option label="管理员" value="admin" />
            <el-option label="编辑" value="editor" />
            <el-option label="只读" value="viewer" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddMember = false">取消</el-button>
        <el-button type="primary" @click="handleAddMember">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>
```

- [ ] **Step 5: Update router**

Add workspace routes to `frontend/src/router/index.ts` children array:
```typescript
{
  path: 'workspaces',
  component: () => import('@/views/workspaces/WorkspaceList.vue'),
  meta: { title: '工作空间' },
},
{
  path: 'workspaces/:id',
  component: () => import('@/views/workspaces/WorkspaceDetail.vue'),
  meta: { title: '空间详情' },
},
```

- [ ] **Step 6: Update MainLayout menu**

Add workspace menu item in `frontend/src/layouts/MainLayout.vue` el-menu:
```vue
<el-menu-item index="/workspaces">
  <el-icon><Folder /></el-icon>
  <template #title>工作空间</template>
</el-menu-item>
```

- [ ] **Step 7: Verify**

```bash
docker compose up -d
# Open http://localhost
# Login → should see workspace menu in sidebar
# Click workspaces → create a workspace → see it in list
```

- [ ] **Step 8: Commit**

```bash
git add frontend/src/
git commit -m "feat: frontend workspace pages — list, detail, member management"
```

---

## Task 4: Frontend — Prompt Pages

**Files:**
- Create: `frontend/src/api/prompts.ts`
- Create: `frontend/src/views/prompts/PromptList.vue`
- Create: `frontend/src/views/prompts/PromptCreate.vue`
- Create: `frontend/src/views/prompts/PromptEdit.vue`
- Create: `frontend/src/views/prompts/PromptVersions.vue`
- Modify: `frontend/src/router/index.ts`
- Modify: `frontend/src/layouts/MainLayout.vue`

- [ ] **Step 1: Create prompt API**

`frontend/src/api/prompts.ts`:
```typescript
import request from './request'

export function listPrompts(params: {
  workspace_id: string
  category?: string
  search?: string
  page?: number
  page_size?: number
}) {
  return request.get('/prompts', { params })
}

export function createPrompt(data: {
  workspace_id: string
  title: string
  content: string
  category?: string
  tags?: string[]
}) {
  return request.post('/prompts', data)
}

export function getPrompt(id: string) {
  return request.get(`/prompts/${id}`)
}

export function updatePrompt(id: string, data: {
  title?: string
  content?: string
  category?: string
  tags?: string[]
  is_favorite?: boolean
}) {
  return request.put(`/prompts/${id}`, data)
}

export function deletePrompt(id: string) {
  return request.delete(`/prompts/${id}`)
}

export function listVersions(promptId: string) {
  return request.get(`/prompts/${promptId}/versions`)
}

export function rollbackVersion(promptId: string, version: number) {
  return request.post(`/prompts/${promptId}/rollback/${version}`)
}
```

- [ ] **Step 2: Create PromptList.vue**

`frontend/src/views/prompts/PromptList.vue`:
```vue
<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkspaceStore } from '@/stores/workspace'
import { listPrompts, deletePrompt, updatePrompt } from '@/api/prompts'
import { ElMessage, ElMessageBox } from 'element-plus'

const workspaceStore = useWorkspaceStore()
const router = useRouter()
const prompts = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const search = ref('')
const category = ref('')
const loading = ref(false)

const categories = [
  { label: '全部', value: '' },
  { label: '营销文案', value: 'marketing' },
  { label: '技术文档', value: 'tech_doc' },
  { label: '社交媒体', value: 'social_media' },
]

async function fetchPrompts() {
  if (!workspaceStore.currentWorkspace) return
  loading.value = true
  try {
    const data: any = await listPrompts({
      workspace_id: workspaceStore.currentWorkspace.id,
      category: category.value || undefined,
      search: search.value || undefined,
      page: page.value,
      page_size: pageSize.value,
    })
    prompts.value = data.data.items
    total.value = data.data.total
  } finally {
    loading.value = false
  }
}

onMounted(fetchPrompts)
watch([page, category], fetchPrompts)

async function handleSearch() {
  page.value = 1
  await fetchPrompts()
}

async function handleDelete(id: string) {
  await ElMessageBox.confirm('确定删除此 Prompt？', '提示', { type: 'warning' })
  await deletePrompt(id)
  ElMessage.success('已删除')
  await fetchPrompts()
}

async function handleToggleFavorite(prompt: any) {
  await updatePrompt(prompt.id, { is_favorite: !prompt.is_favorite })
  await fetchPrompts()
}

function goEdit(id: string) {
  router.push(`/prompts/${id}/edit`)
}

function goVersions(id: string) {
  router.push(`/prompts/${id}/versions`)
}
</script>

<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
      <h3>Prompt 模板</h3>
      <el-button type="primary" @click="router.push('/prompts/create')">新建 Prompt</el-button>
    </div>

    <div style="display: flex; gap: 12px; margin-bottom: 16px;">
      <el-input v-model="search" placeholder="搜索 Prompt..." style="width: 300px;" @keyup.enter="handleSearch" clearable />
      <el-select v-model="category" placeholder="分类" clearable>
        <el-option v-for="c in categories" :key="c.value" :label="c.label" :value="c.value" />
      </el-select>
    </div>

    <el-table :data="prompts" v-loading="loading" style="width: 100%">
      <el-table-column width="40">
        <template #default="{ row }">
          <el-icon style="cursor: pointer;" @click="handleToggleFavorite(row)">
            <StarFilled v-if="row.is_favorite" style="color: #f7ba2a;" />
            <Star v-else />
          </el-icon>
        </template>
      </el-table-column>
      <el-table-column prop="title" label="标题" />
      <el-table-column prop="category" label="分类" width="120" />
      <el-table-column prop="version" label="版本" width="80" />
      <el-table-column label="标签" width="200">
        <template #default="{ row }">
          <el-tag v-for="tag in (row.tags || [])" :key="tag" size="small" style="margin-right: 4px;">{{ tag }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="240">
        <template #default="{ row }">
          <el-button size="small" @click="goEdit(row.id)">编辑</el-button>
          <el-button size="small" @click="goVersions(row.id)">历史</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div style="margin-top: 16px; display: flex; justify-content: flex-end;">
      <el-pagination v-model:current-page="page" :page-size="pageSize" :total="total" layout="prev, pager, next" />
    </div>
  </div>
</template>
```

- [ ] **Step 3: Create PromptCreate.vue**

`frontend/src/views/prompts/PromptCreate.vue`:
```vue
<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkspaceStore } from '@/stores/workspace'
import { createPrompt } from '@/api/prompts'
import { ElMessage } from 'element-plus'

const router = useRouter()
const workspaceStore = useWorkspaceStore()
const loading = ref(false)

const form = ref({
  title: '',
  content: '',
  category: '',
  tags: [] as string[],
  tagInput: '',
})

const categories = [
  { label: '营销文案', value: 'marketing' },
  { label: '技术文档', value: 'tech_doc' },
  { label: '社交媒体', value: 'social_media' },
]

function addTag() {
  const tag = form.value.tagInput.trim()
  if (tag && !form.value.tags.includes(tag)) {
    form.value.tags.push(tag)
  }
  form.value.tagInput = ''
}

function removeTag(tag: string) {
  form.value.tags = form.value.tags.filter((t) => t !== tag)
}

async function handleSubmit() {
  if (!form.value.title || !form.value.content) {
    ElMessage.warning('请填写标题和内容')
    return
  }
  if (!workspaceStore.currentWorkspace) {
    ElMessage.warning('请先选择工作空间')
    return
  }
  loading.value = true
  try {
    await createPrompt({
      workspace_id: workspaceStore.currentWorkspace.id,
      title: form.value.title,
      content: form.value.content,
      category: form.value.category || undefined,
      tags: form.value.tags.length > 0 ? form.value.tags : undefined,
    })
    ElMessage.success('创建成功')
    router.push('/prompts')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
    <h3>新建 Prompt</h3>
    <el-form label-width="80px" style="max-width: 800px; margin-top: 16px;">
      <el-form-item label="标题">
        <el-input v-model="form.title" placeholder="Prompt 标题" />
      </el-form-item>
      <el-form-item label="分类">
        <el-select v-model="form.category" placeholder="选择分类" clearable>
          <el-option v-for="c in categories" :key="c.value" :label="c.label" :value="c.value" />
        </el-select>
      </el-form-item>
      <el-form-item label="标签">
        <div>
          <el-tag v-for="tag in form.tags" :key="tag" closable @close="removeTag(tag)" style="margin-right: 4px; margin-bottom: 4px;">{{ tag }}</el-tag>
          <el-input v-model="form.tagInput" size="small" style="width: 120px;" placeholder="添加标签" @keyup.enter="addTag" />
        </div>
      </el-form-item>
      <el-form-item label="内容">
        <el-input v-model="form.content" type="textarea" :rows="10" placeholder="Prompt 内容，使用 {{变量名}} 定义变量" />
      </el-form-item>
      <el-form-item>
        <p style="color: #999; font-size: 12px;">提示：在内容中使用 {{变量名}} 来定义变量，例如 {{product_name}}、{{target_audience}}</p>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="loading" @click="handleSubmit">创建</el-button>
        <el-button @click="router.push('/prompts')">取消</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>
```

- [ ] **Step 4: Create PromptEdit.vue**

`frontend/src/views/prompts/PromptEdit.vue`:
```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getPrompt, updatePrompt } from '@/api/prompts'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const form = ref({
  title: '',
  content: '',
  category: '',
  tags: [] as string[],
  tagInput: '',
})

const categories = [
  { label: '营销文案', value: 'marketing' },
  { label: '技术文档', value: 'tech_doc' },
  { label: '社交媒体', value: 'social_media' },
]

onMounted(async () => {
  const data: any = await getPrompt(route.params.id as string)
  form.value.title = data.title
  form.value.content = data.content
  form.value.category = data.category || ''
  form.value.tags = data.tags || []
})

function addTag() {
  const tag = form.value.tagInput.trim()
  if (tag && !form.value.tags.includes(tag)) {
    form.value.tags.push(tag)
  }
  form.value.tagInput = ''
}

function removeTag(tag: string) {
  form.value.tags = form.value.tags.filter((t) => t !== tag)
}

async function handleSubmit() {
  if (!form.value.title || !form.value.content) {
    ElMessage.warning('请填写标题和内容')
    return
  }
  loading.value = true
  try {
    await updatePrompt(route.params.id as string, {
      title: form.value.title,
      content: form.value.content,
      category: form.value.category || undefined,
      tags: form.value.tags.length > 0 ? form.value.tags : undefined,
    })
    ElMessage.success('保存成功')
    router.push('/prompts')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
    <h3>编辑 Prompt</h3>
    <el-form label-width="80px" style="max-width: 800px; margin-top: 16px;">
      <el-form-item label="标题">
        <el-input v-model="form.title" />
      </el-form-item>
      <el-form-item label="分类">
        <el-select v-model="form.category" clearable>
          <el-option v-for="c in categories" :key="c.value" :label="c.label" :value="c.value" />
        </el-select>
      </el-form-item>
      <el-form-item label="标签">
        <div>
          <el-tag v-for="tag in form.tags" :key="tag" closable @close="removeTag(tag)" style="margin-right: 4px; margin-bottom: 4px;">{{ tag }}</el-tag>
          <el-input v-model="form.tagInput" size="small" style="width: 120px;" placeholder="添加标签" @keyup.enter="addTag" />
        </div>
      </el-form-item>
      <el-form-item label="内容">
        <el-input v-model="form.content" type="textarea" :rows="10" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="loading" @click="handleSubmit">保存</el-button>
        <el-button @click="router.push('/prompts')">取消</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>
```

- [ ] **Step 5: Create PromptVersions.vue**

`frontend/src/views/prompts/PromptVersions.vue`:
```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { listVersions, rollbackVersion } from '@/api/prompts'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const versions = ref<any[]>([])

onMounted(async () => {
  versions.value = await listVersions(route.params.id as string) as any
})

async function handleRollback(version: number) {
  await ElMessageBox.confirm(`确定回滚到版本 ${version}？`, '提示', { type: 'warning' })
  await rollbackVersion(route.params.id as string, version)
  ElMessage.success('回滚成功')
  router.push('/prompts')
}
</script>

<template>
  <div>
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
      <h3>版本历史</h3>
      <el-button @click="router.push('/prompts')">返回列表</el-button>
    </div>

    <el-timeline>
      <el-timeline-item v-for="v in versions" :key="v.id" :timestamp="new Date(v.created_at).toLocaleString()">
        <el-card>
          <h4>版本 {{ v.version }}</h4>
          <el-input type="textarea" :model-value="v.content" :rows="4" readonly />
          <el-button size="small" style="margin-top: 8px;" @click="handleRollback(v.version)">回滚到此版本</el-button>
        </el-card>
      </el-timeline-item>
    </el-timeline>
  </div>
</template>
```

- [ ] **Step 6: Update router**

Add prompt routes to `frontend/src/router/index.ts` children:
```typescript
{
  path: 'prompts',
  component: () => import('@/views/prompts/PromptList.vue'),
  meta: { title: 'Prompt 管理' },
},
{
  path: 'prompts/create',
  component: () => import('@/views/prompts/PromptCreate.vue'),
  meta: { title: '新建 Prompt' },
},
{
  path: 'prompts/:id/edit',
  component: () => import('@/views/prompts/PromptEdit.vue'),
  meta: { title: '编辑 Prompt' },
},
{
  path: 'prompts/:id/versions',
  component: () => import('@/views/prompts/PromptVersions.vue'),
  meta: { title: '版本历史' },
},
```

- [ ] **Step 7: Update MainLayout menu**

Add prompt menu item:
```vue
<el-menu-item index="/prompts">
  <el-icon><Document /></el-icon>
  <template #title>Prompt 管理</template>
</el-menu-item>
```

- [ ] **Step 8: Verify**

```bash
docker compose up -d
# Login → Create workspace → Go to Prompts → Create a prompt with {{variables}}
# Edit it → Check version history → Rollback
```

- [ ] **Step 9: Commit**

```bash
git add frontend/src/
git commit -m "feat: frontend prompt pages — list, create, edit, version history"
```

---

## Plan 2 Complete

After this plan, you have:
- Workspace CRUD with member management
- Prompt CRUD with `{{variable}}` extraction
- Prompt version history and rollback
- Frontend pages for all workspace and prompt operations
- Search, filter, pagination for prompts
- Favorite/pin prompts

**Next: Plan 3 — AI Model Config + Content Generation**
