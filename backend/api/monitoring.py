"""
Monitoring API Endpoints.
Handles vision inference feeds, trip session control, and overall driver monitoring status.
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
from backend.schemas.vision_schema import VisionEventSchema
from backend.schemas.risk_schema import RiskStateSchema
from backend.services.session_manager import session_manager

router = APIRouter(prefix="/monitoring", tags=["Driver Monitoring"])


@router.post(
    "/vision",
    response_model=RiskStateSchema,
    summary="Ingest Vision Inference Telemetry",
    description="Submits a processed frame event from the AI vision service and updates risk state.",
)
async def ingest_vision_event(event: VisionEventSchema) -> RiskStateSchema:
    try:
        new_risk = session_manager.update_vision(event)
        return new_risk
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process vision telemetry: {str(exc)}",
        )


@router.get(
    "/status",
    response_model=Dict[str, Any],
    summary="Get Current Monitoring Status",
    description="Returns composite real-time telemetry, trip duration, and active risk state.",
)
async def get_current_status() -> Dict[str, Any]:
    return session_manager.get_current_status()


@router.post(
    "/session/start",
    summary="Start Driver Monitoring Session",
    description="Begins trip tracking for fatigue accumulation and event logging.",
)
async def start_session(driver_id: str = "driver_default") -> Dict[str, Any]:
    return session_manager.start_session(driver_id)


@router.post(
    "/session/end",
    summary="End Driver Monitoring Session",
    description="Concludes active trip and returns trip duration summary.",
)
async def end_session() -> Dict[str, Any]:
    return session_manager.end_session()
