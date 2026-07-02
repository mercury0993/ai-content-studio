import time
import uuid
from typing import AsyncGenerator

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content, ContentStatus
from app.models.prompt import Prompt
from app.models.ai_model import AIModel
from app.schemas.content import ContentGenerate, ContentUpdate
from app.services import ai_service


async def generate_content(db: AsyncSession, user_id: uuid.UUID, req: ContentGenerate) -> Content:
    prompt_result = await db.execute(select(Prompt).where(Prompt.id == req.prompt_id, Prompt.workspace_id == req.workspace_id))
    prompt = prompt_result.scalar_one_or_none()
    if not prompt:
        raise ValueError("Prompt not found")

    model_result = await db.execute(select(AIModel).where(AIModel.id == req.model_id, AIModel.workspace_id == req.workspace_id))
    model = model_result.scalar_one_or_none()
    if not model:
        raise ValueError("Model not found")

    prompt_text = ai_service.build_prompt_text(prompt.content, req.variables)
    ai_result = await ai_service.deepseek_generate(prompt_text, model)

    content = Content(
        workspace_id=req.workspace_id,
        prompt_id=req.prompt_id,
        model_id=req.model_id,
        variables_used=req.variables or {},
        generated_text=ai_result["generated_text"],
        status=ContentStatus.DRAFT,
        token_usage=ai_result["token_usage"],
        generation_time_ms=ai_result["generation_time_ms"],
        created_by=user_id,
    )
    db.add(content)
    await db.flush()
    return content


async def generate_content_stream(db: AsyncSession, user_id: uuid.UUID, req: ContentGenerate) -> AsyncGenerator[str, None]:
    prompt_result = await db.execute(select(Prompt).where(Prompt.id == req.prompt_id, Prompt.workspace_id == req.workspace_id))
    prompt = prompt_result.scalar_one_or_none()
    if not prompt:
        raise ValueError("Prompt not found")

    model_result = await db.execute(select(AIModel).where(AIModel.id == req.model_id, AIModel.workspace_id == req.workspace_id))
    model = model_result.scalar_one_or_none()
    if not model:
        raise ValueError("Model not found")

    prompt_text = ai_service.build_prompt_text(prompt.content, req.variables)

    start_time = time.time()
    full_text = ""

    async for chunk in ai_service.deepseek_generate_stream(prompt_text, model):
        full_text += chunk
        yield chunk

    # Save generated content to DB after stream completes
    generation_time_ms = int((time.time() - start_time) * 1000)
    content = Content(
        workspace_id=req.workspace_id,
        prompt_id=req.prompt_id,
        model_id=req.model_id,
        variables_used=req.variables or {},
        generated_text=full_text,
        status=ContentStatus.DRAFT,
        token_usage=0,
        generation_time_ms=generation_time_ms,
        created_by=user_id,
    )
    db.add(content)
    await db.flush()
    yield f"\n__CID__:{content.id}\n"


async def list_contents(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Content], int]:
    query = select(Content).where(Content.workspace_id == workspace_id)
    if status:
        query = query.where(Content.status == ContentStatus(status))

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    query = query.order_by(Content.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return list(result.scalars().all()), total


async def get_content(db: AsyncSession, content_id: uuid.UUID) -> Content | None:
    result = await db.execute(select(Content).where(Content.id == content_id))
    return result.scalar_one_or_none()


async def update_content(db: AsyncSession, content_id: uuid.UUID, req: ContentUpdate) -> Content:
    content = await get_content(db, content_id)
    if not content:
        raise ValueError("Content not found")
    if req.edited_text is not None:
        content.edited_text = req.edited_text
    await db.flush()
    await db.refresh(content)
    return content


async def delete_content(db: AsyncSession, content_id: uuid.UUID) -> None:
    content = await get_content(db, content_id)
    if not content:
        raise ValueError("Content not found")
    await db.delete(content)
    await db.flush()
