"""
Extreme IP Guard - Advanced Network Security Platform
Backend API Server
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
from loguru import logger

from app.core.config import settings
from app.routers import auth, monitoring, analytics, policies
from app.services.monitor_service import get_monitoring_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("=" * 60)
    logger.info(f"  {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info("  Advanced AI-Powered Network Security Platform")
    logger.info("=" * 60)
    
    # Auto-start monitoring
    monitoring_service = get_monitoring_service()
    await monitoring_service.start()
    logger.info("Real-time monitoring engine started")
    
    yield
    
    # Cleanup
    await monitoring_service.stop()
    logger.info("Monitoring engine stopped. Goodbye.")


app = FastAPI(
    title=settings.APP_NAME,
    description="""
## Extreme IP Guard - Next Generation Network Security Platform

An advanced AI/ML-powered network security system with:

- **Real-time threat detection** using ensemble ML models
- **Behavioral analytics** (UEBA) with anomaly detection  
- **Threat intelligence** integration and reputation scoring
- **MITRE ATT&CK** framework mapping
- **Zero Trust** architecture enforcement
- **Automated response** and IP blocking
- **WebSocket** real-time streaming dashboard

### Default Credentials
- Admin: `admin` / `Admin@2026!`
- Analyst: `analyst` / `Analyst@2026!`
    """,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
    response.headers["X-Powered-By"] = "Extreme IP Guard v2.0"
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": type(exc).__name__},
    )


# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(monitoring.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(policies.router, prefix="/api")


@app.get("/api/health")
async def health_check():
    return {
        "status": "operational",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": time.time(),
    }


@app.get("/api")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "AI-Powered Network Security Platform",
        "docs": "/api/docs",
        "status": "operational",
    }
