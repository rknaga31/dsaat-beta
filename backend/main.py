"""
Main FastAPI Application Entry Point.
Multimodal Driver Drowsiness and Health Monitoring System Backend.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config.settings import get_settings
from backend.api.routes import api_router
from backend.services.event_logger import event_logger

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown procedures."""
    # Startup: Log system initialization
    event_logger.log_event(
        "system_startup",
        {
            "env": settings.APP_ENV,
            "host": settings.BACKEND_HOST,
            "port": settings.BACKEND_PORT,
            "sms_provider": settings.SMS_PROVIDER,
            "smartwatch_source": settings.SMARTWATCH_SOURCE,
        },
    )
    yield
    # Shutdown
    event_logger.log_event("system_shutdown", {"status": "clean_exit"})


app = FastAPI(
    title="Multimodal Driver Drowsiness & Health Monitoring System",
    description=(
        "Backend API service for real-time computer vision inference ingestion, "
        "smartwatch telemetry integration, multimodal risk evaluation, and emergency SOS alerts."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Cross-Origin Resource Sharing (CORS) Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS or ["*"],
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(api_router)


@app.get("/", tags=["Health"])
async def root():
    """Root status greeting endpoint."""
    return {
        "system": "Multimodal Driver Drowsiness and Health Monitoring System",
        "status": "OPERATIONAL",
        "version": "1.0.0",
        "docs_url": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """System health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "env": settings.APP_ENV,
        "sms_provider": settings.SMS_PROVIDER,
        "smartwatch_source": settings.SMARTWATCH_SOURCE,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG,
    )
