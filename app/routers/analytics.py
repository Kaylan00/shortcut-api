import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_user
from app.database import get_db
from app.models import Click, Link, User
from app.schemas import ClickOut, LinkAnalytics

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])


@router.get("/{link_id}", response_model=LinkAnalytics)
async def get_analytics(
    link_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Link)
        .where(Link.id == link_id, Link.owner_id == current_user.id)
        .options(selectinload(Link.clicks))
    )
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="Link nao encontrado")

    now = datetime.datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - datetime.timedelta(days=now.weekday())
    month_start = today_start.replace(day=1)

    def _naive(dt: datetime.datetime) -> datetime.datetime:
        return dt.replace(tzinfo=None) if dt.tzinfo else dt

    clicks_today = sum(1 for c in link.clicks if c.clicked_at and _naive(c.clicked_at) >= today_start)
    clicks_week = sum(1 for c in link.clicks if c.clicked_at and _naive(c.clicked_at) >= week_start)
    clicks_month = sum(1 for c in link.clicks if c.clicked_at and _naive(c.clicked_at) >= month_start)

    referrer_count: dict[str, int] = {}
    for c in link.clicks:
        ref = c.referrer or "Direto"
        referrer_count[ref] = referrer_count.get(ref, 0) + 1

    top_referrers = [
        {"referrer": k, "count": v}
        for k, v in sorted(referrer_count.items(), key=lambda x: x[1], reverse=True)[:10]
    ]

    recent = sorted(link.clicks, key=lambda c: c.clicked_at or now, reverse=True)[:20]

    return LinkAnalytics(
        link_id=link.id,
        short_code=link.short_code,
        original_url=link.original_url,
        total_clicks=len(link.clicks),
        clicks_today=clicks_today,
        clicks_this_week=clicks_week,
        clicks_this_month=clicks_month,
        recent_clicks=[ClickOut.model_validate(c) for c in recent],
        top_referrers=top_referrers,
    )
