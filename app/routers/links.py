import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.models import Click, Link, User
from app.schemas import LinkCreate, LinkOut, LinkUpdate
from app.utils import generate_qr_code, generate_short_code

router = APIRouter(tags=["Links"])


def _link_to_out(link: Link) -> dict:
    return {
        "id": link.id,
        "original_url": link.original_url,
        "short_code": link.short_code,
        "short_url": f"{settings.BASE_URL}/{link.short_code}",
        "title": link.title,
        "is_active": link.is_active,
        "total_clicks": link.total_clicks,
        "created_at": link.created_at,
        "expires_at": link.expires_at,
    }


@router.post("/api/v1/links", response_model=LinkOut, status_code=status.HTTP_201_CREATED)
async def create_link(
    data: LinkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if data.custom_code:
        result = await db.execute(select(Link).where(Link.short_code == data.custom_code))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Esse codigo customizado ja esta em uso")
        short_code = data.custom_code
    else:
        short_code = await generate_short_code(db)

    link = Link(
        original_url=str(data.original_url),
        short_code=short_code,
        title=data.title,
        expires_at=data.expires_at,
        owner_id=current_user.id,
    )
    db.add(link)
    await db.commit()
    await db.refresh(link, attribute_names=["clicks"])
    return _link_to_out(link)


@router.get("/api/v1/links", response_model=list[LinkOut])
async def list_links(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Link)
        .where(Link.owner_id == current_user.id)
        .options(selectinload(Link.clicks))
        .order_by(Link.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    links = result.scalars().all()
    return [_link_to_out(link) for link in links]


@router.get("/api/v1/links/{link_id}", response_model=LinkOut)
async def get_link(
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
    return _link_to_out(link)


@router.patch("/api/v1/links/{link_id}", response_model=LinkOut)
async def update_link(
    link_id: int,
    data: LinkUpdate,
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

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(link, field, value)

    await db.commit()
    await db.refresh(link, attribute_names=["clicks"])
    return _link_to_out(link)


@router.delete("/api/v1/links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_link(
    link_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Link).where(Link.id == link_id, Link.owner_id == current_user.id)
    )
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="Link nao encontrado")

    await db.delete(link)
    await db.commit()


@router.get("/api/v1/links/{link_id}/qrcode")
async def get_qr_code(
    link_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Link).where(Link.id == link_id, Link.owner_id == current_user.id)
    )
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="Link nao encontrado")

    short_url = f"{settings.BASE_URL}/{link.short_code}"
    qr_bytes = generate_qr_code(short_url)
    return Response(content=qr_bytes, media_type="image/png")


@router.get("/{short_code}")
async def redirect_to_url(
    short_code: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Link).where(Link.short_code == short_code))
    link = result.scalar_one_or_none()

    if not link or not link.is_active:
        raise HTTPException(status_code=404, detail="Link nao encontrado ou desativado")

    now = datetime.datetime.now(datetime.timezone.utc)
    if link.expires_at and link.expires_at.replace(tzinfo=now.tzinfo) < now:
        raise HTTPException(status_code=410, detail="Link expirado")

    click = Click(
        link_id=link.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        referrer=request.headers.get("referer"),
    )
    db.add(click)
    await db.commit()

    return RedirectResponse(url=link.original_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
