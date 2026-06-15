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
    member = await workspace_service.check_workspace_access(db, prompt.workspace_id, current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this workspace")
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
