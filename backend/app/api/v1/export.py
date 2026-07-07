import io
import uuid
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.services import workspace_service, export_service


def _safe_content_disposition(filename: str) -> str:
    """Build a Content-Disposition header value that supports non-ASCII filenames."""
    encoded = quote(filename, safe="")
    return f"attachment; filename*=UTF-8''{encoded}"

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/markdown/{content_id}")
async def export_markdown(
    content_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    content, text = await export_service.get_content_for_export(db, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    if not text:
        raise HTTPException(status_code=400, detail="Only approved content can be exported")

    member = await workspace_service.check_workspace_access(db, content.workspace_id, current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Not a member")

    filename = await export_service.get_export_filename(db, content)

    return StreamingResponse(
        io.BytesIO(text.encode("utf-8")),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": _safe_content_disposition(filename)},
    )


@router.post("/zip")
async def export_zip(
    content_ids: list[uuid.UUID],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    contents = await export_service.get_contents_by_ids(db, content_ids)
    if not contents:
        raise HTTPException(status_code=404, detail="No contents found")

    for c in contents:
        member = await workspace_service.check_workspace_access(db, c.workspace_id, current_user.id)
        if not member:
            raise HTTPException(status_code=403, detail="Not a member of one or more workspaces")

    zip_buffer = await export_service.build_zip_response(db, contents)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=contents.zip"},
    )
