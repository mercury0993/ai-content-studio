import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func, cast, Date, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content, ContentStatus
from app.models.prompt import Prompt
from app.models.ai_model import AIModel
from app.models.user import User


async def get_stats(db: AsyncSession, workspace_id: uuid.UUID) -> dict:
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Merge 3 Content COUNT queries into 1 using conditional aggregation
    content_result = await db.execute(
        select(
            func.count(Content.id).label("content_count"),
            func.count(case((Content.status == ContentStatus.PENDING_REVIEW, 1))).label("pending_review"),
            func.count(case((Content.created_at >= month_start, 1))).label("monthly_generated"),
        ).where(Content.workspace_id == workspace_id)
    )
    content_row = content_result.one()

    prompt_count = (await db.execute(
        select(func.count()).where(Prompt.workspace_id == workspace_id)
    )).scalar()

    return {
        "prompt_count": prompt_count,
        "content_count": content_row.content_count,
        "monthly_generated": content_row.monthly_generated,
        "pending_review": content_row.pending_review,
    }


async def get_trend(db: AsyncSession, workspace_id: uuid.UUID, days: int = 30) -> list[dict]:
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days)

    result = await db.execute(
        select(
            cast(Content.created_at, Date).label("date"),
            func.count().label("count"),
        )
        .where(
            Content.workspace_id == workspace_id,
            Content.created_at >= start,
        )
        .group_by(cast(Content.created_at, Date))
        .order_by(cast(Content.created_at, Date))
    )

    data_map = {str(row.date): row.count for row in result.all()}
    trend = []
    for i in range(days):
        d = (start + timedelta(days=i)).strftime("%Y-%m-%d")
        trend.append({"date": d, "count": data_map.get(d, 0)})
    return trend


async def get_model_usage(db: AsyncSession, workspace_id: uuid.UUID) -> list[dict]:
    result = await db.execute(
        select(
            AIModel.name,
            func.count(Content.id).label("count"),
        )
        .outerjoin(Content, Content.model_id == AIModel.id)
        .where(AIModel.workspace_id == workspace_id)
        .group_by(AIModel.name)
    )
    return [{"name": row.name, "count": row.count} for row in result.all()]


async def get_user_ranking(db: AsyncSession, workspace_id: uuid.UUID, limit: int = 10) -> list[dict]:
    result = await db.execute(
        select(
            User.username,
            func.count(Content.id).label("count"),
        )
        .outerjoin(Content, Content.created_by == User.id)
        .where(Content.workspace_id == workspace_id)
        .group_by(User.username)
        .order_by(func.count(Content.id).desc())
        .limit(limit)
    )
    return [{"username": row.username, "count": row.count} for row in result.all()]


async def get_recent(db: AsyncSession, workspace_id: uuid.UUID, limit: int = 10) -> list[Content]:
    result = await db.execute(
        select(Content)
        .where(Content.workspace_id == workspace_id)
        .order_by(Content.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
