from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine
from app.models import Base
from app.routers import analytics, links, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="ShortCut API",
    description="API moderna de encurtamento de URLs com analytics e QR Code",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(links.router)
app.include_router(analytics.router)


@app.get("/", tags=["Health"])
async def health_check():
    return {
        "status": "online",
        "app": "ShortCut API",
        "version": "1.0.0",
        "docs": "/docs",
    }
