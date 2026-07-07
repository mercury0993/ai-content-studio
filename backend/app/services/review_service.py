import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content, ContentStatus
from app.models.audit_log import AuditLog
from app.models.workspace import WorkspaceMember, WorkspaceMemberRole


def _log_audit(db: AsyncSession, user_id: uuid.UUID, action: str, resource_type: str, resource_id: uuid.UUID, details: dict | None = None):
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
    )
    db.add(log)


async def submit_for_review(db: AsyncSession, content_id: uuid.UUID, reviewer_id: uuid.UUID | None, user_id: uuid.UUID) -> Content:
    result = await db.execute(select(Content).where(Content.id == content_id))
    content = result.scalar_one_or_none()
    if not content:
        raise ValueError("Content not found")
    if content.status not in (ContentStatus.DRAFT, ContentStatus.REJECTED):
        raise ValueError(f"Cannot submit content with status '{content.status}'")

    # Auto-assign reviewer to first workspace admin if not specified
    resolved_reviewer_id = reviewer_id
    if not resolved_reviewer_id:
        admin_result = await db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == content.workspace_id,
                WorkspaceMember.role == WorkspaceMemberRole.ADMIN,
            ).limit(1)
        )
        admin = admin_result.scalar_one_or_none()
        if admin:
            resolved_reviewer_id = admin.user_id
        else:
            resolved_reviewer_id = user_id  # fallback to the submitter

    old_status = content.status.value
    content.status = ContentStatus.PENDING_REVIEW
    content.reviewed_by = resolved_reviewer_id
    content.review_comment = None
    await db.flush()

    _log_audit(db, user_id, "content.submit", "content", content_id, {"from": old_status, "to": "pending_review"})
    await db.flush()
    await db.refresh(content)
    return content


async def approve_content(db: AsyncSession, content_id: uuid.UUID, reviewer_id: uuid.UUID, comment: str | None = None) -> Content:
    result = await db.execute(select(Content).where(Content.id == content_id))
    content = result.scalar_one_or_none()
    if not content:
        raise ValueError("Content not found")
    if content.status != ContentStatus.PENDING_REVIEW:
        raise ValueError("Content is not pending review")

    content.status = ContentStatus.APPROVED
    content.reviewed_by = reviewer_id
    content.review_comment = comment
    content.reviewed_at = datetime.now(timezone.utc)
    await db.flush()

    _log_audit(db, reviewer_id, "content.approve", "content", content_id, {"comment": comment})
    await db.flush()
    await db.refresh(content)
    return content


async def reject_content(db: AsyncSession, content_id: uuid.UUID, reviewer_id: uuid.UUID, comment: str | None = None) -> Content:
    result = await db.execute(select(Content).where(Content.id == content_id))
    content = result.scalar_one_or_none()
    if not content:
        raise ValueError("Content not found")
    if content.status != ContentStatus.PENDING_REVIEW:
        raise ValueError("Content is not pending review")
    if not comment:
        raise ValueError("Rejection requires a comment")

    content.status = ContentStatus.REJECTED
    content.reviewed_by = reviewer_id
    content.review_comment = comment
    content.reviewed_at = datetime.now(timezone.utc)
    await db.flush()

    _log_audit(db, reviewer_id, "content.reject", "content", content_id, {"comment": comment})
    await db.flush()
    await db.refresh(content)
    return content


async def batch_review(db: AsyncSession, content_ids: list[uuid.UUID], action: str, reviewer_id: uuid.UUID, comment: str | None = None) -> int:
    try:
        # Fetch all contents in one query to avoid N+1
        result = await db.execute(select(Content).where(Content.id.in_(content_ids)))
        content_map = {c.id: c for c in result.scalars().all()}

        count = 0
        for cid in content_ids:
            content = content_map.get(cid)
            if not content:
                raise ValueError(f"Content {cid} not found")
            if content.status != ContentStatus.PENDING_REVIEW:
                continue
            if action == "reject" and not comment:
                continue

            content.status = ContentStatus.APPROVED if action == "approve" else ContentStatus.REJECTED
            content.reviewed_by = reviewer_id
            content.review_comment = comment
            content.reviewed_at = datetime.now(timezone.utc)
            _log_audit(db, reviewer_id, f"content.{action}", "content", cid, {"comment": comment})
            count += 1

        await db.flush()
        return count
    except Exception:
        await db.rollback()
        raise


async def list_reviews(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Content], int]:
    query = select(Content).where(Content.workspace_id == workspace_id)
    if status:
        query = query.where(Content.status == ContentStatus(status))
    else:
        query = query.where(Content.status == ContentStatus.PENDING_REVIEW)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    query = query.order_by(Content.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return list(result.scalars().all()), total