import io
import uuid
import zipfile

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content, ContentStatus
from app.models.prompt import Prompt


async def get_content_for_export(db: AsyncSession, content_id: uuid.UUID) -> tuple[Content | None, str | None]:
    result = await db.execute(select(Content).where(Content.id == content_id))
    content = result.scalar_one_or_none()
    if not content or content.status != ContentStatus.APPROVED:
        return content, None

    text = content.edited_text or content.generated_text
    return content, text


async def get_export_filename(db: AsyncSession, content: Content) -> str:
    prompt_result = await db.execute(select(Prompt).where(Prompt.id == content.prompt_id))
    prompt = prompt_result.scalar_one_or_none()
    prefix = prompt.title if prompt else "content"
    return f"{prefix}_{str(content.id)[:8]}.md"


async def get_contents_by_ids(db: AsyncSession, content_ids: list[uuid.UUID]) -> list[Content]:
    result = await db.execute(select(Content).where(Content.id.in_(content_ids)))
    return list(result.scalars().all())


async def build_zip_response(db: AsyncSession, contents: list[Content]) -> io.BytesIO:
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for content in contents:
            text = content.edited_text or content.generated_text
            prompt_result = await db.execute(select(Prompt).where(Prompt.id == content.prompt_id))
            prompt = prompt_result.scalar_one_or_none()
            filename = f"{prompt.title if prompt else 'content'}_{str(content.id)[:8]}.md"
            zf.writestr(filename, text)
    zip_buffer.seek(0)
    return zip_buffer
