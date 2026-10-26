"""
API Master Router.
Aggregates monitoring, sensors, and alerts sub-routers into a unified /api/v1 tree.
"""

from fastapi import APIRouter
from backend.api.monitoring import router as monitoring_router
from backend.api.sensors import router as sensors_router
from backend.api.alerts import router as alerts_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(monitoring_router)
api_router.include_router(sensors_router)
api_router.include_router(alerts_router)
