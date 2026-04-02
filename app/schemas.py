import datetime

from pydantic import BaseModel, EmailStr, HttpUrl


# ── Auth / Users ──────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── Links ─────────────────────────────────────────────────────

class LinkCreate(BaseModel):
    original_url: HttpUrl
    title: str | None = None
    custom_code: str | None = None
    expires_at: datetime.datetime | None = None


class LinkUpdate(BaseModel):
    title: str | None = None
    is_active: bool | None = None
    expires_at: datetime.datetime | None = None


class LinkOut(BaseModel):
    id: int
    original_url: str
    short_code: str
    short_url: str
    title: str | None
    is_active: bool
    total_clicks: int
    created_at: datetime.datetime
    expires_at: datetime.datetime | None

    model_config = {"from_attributes": True}


# ── Analytics ─────────────────────────────────────────────────

class ClickOut(BaseModel):
    id: int
    clicked_at: datetime.datetime
    ip_address: str | None
    user_agent: str | None
    referrer: str | None

    model_config = {"from_attributes": True}


class LinkAnalytics(BaseModel):
    link_id: int
    short_code: str
    original_url: str
    total_clicks: int
    clicks_today: int
    clicks_this_week: int
    clicks_this_month: int
    recent_clicks: list[ClickOut]
    top_referrers: list[dict]
