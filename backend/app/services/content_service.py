import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content, ContentStatus
from app.models.prompt import Prompt
from app.schemas.content import ContentGenerate, ContentUpdate
from app.services.ai_service import mock_generate


async def generate_content(db: AsyncSession, user_id: uuid.UUID, req: ContentGenerate) -> Content:
    result = await db.execute(select(Prompt).where(Prompt.id == req.prompt_id))
    prompt = result.scalar_one_or_none()
    if not prompt:
        raise ValueError("Prompt not found")

    ai_result = mock_generate(prompt.category, req.variables, prompt.title)

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
