import re
import uuid

from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prompt import Prompt, PromptVersion
from app.schemas.prompt import PromptCreate, PromptUpdate


def extract_variables(content: str) -> list[dict]:
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

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

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
