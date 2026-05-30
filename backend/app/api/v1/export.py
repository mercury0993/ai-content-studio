import io
import uuid
import zipfile

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.content import Content, ContentStatus
from app.models.prompt import Prompt
from app.services import workspace_service

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/markdown/{content_id}")
async def export_markdown(
    content_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Content).where(Content.id == content_id))
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    if content.status != ContentStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Only approved content can be exported")

    member = await workspace_service.check_workspace_access(db, content.workspace_id, current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Not a member")

    text = content.edited_text or content.generated_text
    prompt_result = await db.execute(select(Prompt).where(Prompt.id == content.prompt_id))
    prompt = prompt_result.scalar_one_or_none()
    filename = f"{prompt.title if prompt else 'content'}_{str(content.id)[:8]}.md"

    return StreamingResponse(
        io.BytesIO(text.encode("utf-8")),
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/zip")
async def export_zip(
    content_ids: list[uuid.UUID],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Content).where(Content.id.in_(content_ids)))
    contents = list(result.scalars().all())

    if not contents:
        raise HTTPException(status_code=404, detail="No contents found")

    for c in contents:
        member = await workspace_service.check_workspace_access(db, c.workspace_id, current_user.id)
        if not member:
            raise HTTPException(status_code=403, detail="Not a member of one or more workspaces")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for content in contents:
            text = content.edited_text or content.generated_text
            prompt_result = await db.execute(select(Prompt).where(Prompt.id == content.prompt_id))
            prompt = prompt_result.scalar_one_or_none()
            filename = f"{prompt.title if prompt else 'content'}_{str(content.id)[:8]}.md"
            zf.writestr(filename, text)

    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=contents.zip"},
    )
