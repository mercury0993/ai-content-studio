import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.ai_model import AIModelCreate, AIModelUpdate, AIModelResponse
from app.services import ai_model_service, workspace_service

router = APIRouter(prefix="/models", tags=["models"])


@router.get("", response_model=list[AIModelResponse])
async def list_models(
    workspace_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await workspace_service.check_workspace_access(db, workspace_id, current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Not a member")
    return await ai_model_service.list_models(db, workspace_id)


@router.post("", response_model=AIModelResponse)
async def create_model(
    req: AIModelCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await workspace_service.check_workspace_access(db, req.workspace_id, current_user.id)
    if not member or member.role.value == "viewer":
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return await ai_model_service.create_model(db, req)


@router.get("/{model_id}", response_model=AIModelResponse)
async def get_model(model_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    model = await ai_model_service.get_model(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    member = await workspace_service.check_workspace_access(db, model.workspace_id, current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this workspace")
    return model


@router.put("/{model_id}", response_model=AIModelResponse)
async def update_model(
    model_id: uuid.UUID,
    req: AIModelUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    model = await ai_model_service.get_model(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    member = await workspace_service.check_workspace_access(db, model.workspace_id, current_user.id)
    if not member or member.role.value == "viewer":
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    try:
        return await ai_model_service.update_model(db, model_id, req)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{model_id}")
async def delete_model(model_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    model = await ai_model_service.get_model(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    member = await workspace_service.check_workspace_access(db, model.workspace_id, current_user.id)
    if not member or member.role.value == "viewer":
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    try:
        await ai_model_service.delete_model(db, model_id)
        return {"message": "Deleted"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{model_id}/toggle", response_model=AIModelResponse)
async def toggle_model(model_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    model = await ai_model_service.get_model(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    member = await workspace_service.check_workspace_access(db, model.workspace_id, current_user.id)
    if not member or member.role.value == "viewer":
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    try:
        return await ai_model_service.toggle_model(db, model_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
