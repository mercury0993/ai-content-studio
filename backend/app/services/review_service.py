import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content, ContentStatus
from app.models.audit_log import AuditLog


def _log_audit(db: AsyncSession, user_id: uuid.UUID, action: str, resource_type: str, resource_id: uuid.UUID, details: dict | None = None):
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
    )
    db.add(log)


async def submit_for_review(db: AsyncSession, content_id: uuid.UUID, reviewer_id: uuid.UUID, user_id: uuid.UUID) -> Content:
    result = await db.execute(select(Content).where(Content.id == content_id))
    content = result.scalar_one_or_none()
    if not content:
        raise ValueError("Content not found")
    if content.status not in (ContentStatus.DRAFT, ContentStatus.REJECTED):
        raise ValueError(f"Cannot submit content with status '{content.status}'")

    old_status = content.status.value
    content.status = ContentStatus.PENDING_REVIEW
    content.reviewed_by = reviewer_id
    content.review_comment = None
    await db.flush()

    _log_audit(db, user_id, "content.submit", "content", content_id, {"from": old_status, "to": "pending_review"})
    await db.flush()
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
    return content


async def batch_review(db: AsyncSession, content_ids: list[uuid.UUID], action: str, reviewer_id: uuid.UUID, comment: str | None = None) -> int:
    count = 0
    for cid in content_ids:
        try:
            if action == "approve":
                await approve_content(db, cid, reviewer_id, comment)
            elif action == "reject":
                await reject_content(db, cid, reviewer_id, comment)
            count += 1
        except ValueError:
            continue
    return count


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