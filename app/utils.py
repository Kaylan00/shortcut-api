import io
import string
import secrets

import qrcode
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Link

ALPHABET = string.ascii_letters + string.digits


async def generate_short_code(db: AsyncSession, length: int = 6) -> str:
    while True:
        code = "".join(secrets.choice(ALPHABET) for _ in range(length))
        result = await db.execute(select(Link).where(Link.short_code == code))
        if result.scalar_one_or_none() is None:
            return code


def generate_qr_code(url: str) -> bytes:
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()
