import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_model import AIModel
from app.schemas.ai_model import AIModelCreate, AIModelUpdate


async def create_model(db: AsyncSession, req: AIModelCreate) -> AIModel:
    model = AIModel(
        workspace_id=req.workspace_id,
        name=req.name,
        provider=req.provider,
        api_key=req.api_key,
        base_url=req.base_url,
        model_name=req.model_name,
        default_params=req.default_params,
    )
    db.add(model)
    await db.flush()
    return model


async def list_models(db: AsyncSession, workspace_id: uuid.UUID) -> list[AIModel]:
    result = await db.execute(
        select(AIModel).where(AIModel.workspace_id == workspace_id).order_by(AIModel.created_at.desc())
    )
    return list(result.scalars().all())


async def get_model(db: AsyncSession, model_id: uuid.UUID) -> AIModel | None:
    result = await db.execute(select(AIModel).where(AIModel.id == model_id))
    return result.scalar_one_or_none()


async def update_model(db: AsyncSession, model_id: uuid.UUID, req: AIModelUpdate) -> AIModel:
    model = await get_model(db, model_id)
    if not model:
        raise ValueError("Model not found")
    if req.name is not None:
        model.name = req.name
    if req.provider is not None:
        model.provider = req.provider
    if req.api_key is not None:
        model.api_key = req.api_key
    if req.base_url is not None:
        model.base_url = req.base_url
    if req.model_name is not None:
        model.model_name = req.model_name
    if req.default_params is not None:
        model.default_params = req.default_params
    await db.flush()
    return model


async def delete_model(db: AsyncSession, model_id: uuid.UUID) -> None:
    model = await get_model(db, model_id)
    if not model:
        raise ValueError("Model not found")
    await db.delete(model)
    await db.flush()


async def toggle_model(db: AsyncSession, model_id: uuid.UUID) -> AIModel:
    model = await get_model(db, model_id)
    if not model:
        raise ValueError("Model not found")
    model.is_active = not model.is_active
    await db.flush()
    return model
