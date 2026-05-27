"""
Extreme IP Guard - Next-Generation Cybersecurity Platform
Main application entry point.
"""

import sys
import os
import asyncio
import uvicorn
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings
from app.models.database import init_db, async_session
from app.api.routes import router as api_router
from app.services.ip_service import IPService
from app.core.network_monitor import network_monitor


async def startup_tasks():
    """Initialize database, seed demo data, and start monitoring."""
    await init_db()

    async with async_session() as db:
        service = IPService(db)
        await service.seed_demo_data()

    await network_monitor.capture_snapshot()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup_tasks()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "app/static")), name="static")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "app/templates"))

app.include_router(api_router)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health_check():
    return {
        "status": "operational",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
