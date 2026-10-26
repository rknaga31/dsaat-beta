"""
Alerts API Endpoints.
Provides alert history, manual emergency SOS trigger, alert acknowledgement,
and emergency contact configuration.
"""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Query, HTTPException, status
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from backend.services.event_logger import event_logger
from backend.services.session_manager import session_manager
from backend.schemas.alert_schema import AlertEventSchema
from shared.constants import (
    AlertLevelEnum,
    BeepStatusEnum,
    SmsStatusEnum,
    LocationStatusEnum,
)

router = APIRouter(prefix="/alerts", tags=["Alerts & SOS"])


class EmergencyContactUpdate(BaseModel):
    phone_number: str = Field(..., description="E.164 phone number, e.g. +919876543210")
    contact_name: Optional[str] = Field(default=None, description="Name of contact")


@router.get(
    "/recent",
    summary="Get Recent Alerts and Events",
    description="Returns chronological audit trail of risk escalations and SOS actions.",
)
async def get_recent_alerts(
    limit: int = Query(default=30, ge=1, le=100),
    event_type: str = Query(default=None),
) -> List[Dict[str, Any]]:
    return event_logger.get_recent_events(limit=limit, event_type=event_type)


@router.post(
    "/sos",
    response_model=AlertEventSchema,
    summary="Manual Emergency SOS Trigger",
    description="Allows driver or copilot to trigger an immediate high-priority SOS alert.",
)
async def trigger_manual_sos(reason: str = "Driver manual SOS button pressed") -> AlertEventSchema:
    now_iso = datetime.now(timezone.utc).isoformat()
    lat = session_manager.latest_latitude
    lon = session_manager.latest_longitude

    # Dispatch immediately via family service
    sms_status, _ = session_manager.escalation_manager.family_service.dispatch_sos(
        driver_name="Primary Driver",
        reason=reason,
        latitude=lat,
        longitude=lon,
    )
    beep_status = session_manager.escalation_manager.beep_manager.play_warning(AlertLevelEnum.CRITICAL)

    alert = AlertEventSchema(
        event_id=str(uuid.uuid4()),
        timestamp=now_iso,
        alert_level=AlertLevelEnum.CRITICAL,
        reason=reason,
        driver_beep_status=beep_status,
        family_sms_status=sms_status,
        location_status=LocationStatusEnum.AVAILABLE if lat is not None else LocationStatusEnum.UNAVAILABLE,
        latitude=lat,
        longitude=lon,
    )
    session_manager.latest_alert = alert
    event_logger.log_event("manual_sos_triggered", alert.model_dump())
    return alert


@router.post(
    "/acknowledge",
    summary="Acknowledge Active Alert",
    description="Silences cabin buzzer and cancels pending family SMS escalation.",
)
async def acknowledge_alert() -> Dict[str, Any]:
    return session_manager.acknowledge_alert()


@router.post(
    "/contact",
    summary="Configure Family Emergency Contact",
    description="Updates the recipient phone number and contact name for SMS alerts.",
)
async def update_contact(payload: EmergencyContactUpdate) -> Dict[str, Any]:
    session_manager.escalation_manager.family_service.update_contact(
        phone=payload.phone_number,
        name=payload.contact_name,
    )
    return {
        "status": "UPDATED",
        "phone_number": payload.phone_number,
        "contact_name": session_manager.escalation_manager.family_service.emergency_contact_name,
    }


@router.post(
    "/test-beep",
    summary="Test In-Cabin Acoustic Buzzer",
    description="Emits a single test tone through laptop speakers without changing risk state.",
)
async def test_buzzer(level: str = "WARNING") -> Dict[str, Any]:
    lvl = AlertLevelEnum.CRITICAL if level.upper() == "CRITICAL" else AlertLevelEnum.WARNING
    status_result = session_manager.escalation_manager.beep_manager.play_warning(lvl)
    return {
        "status": status_result.value,
        "level": lvl.value,
        "message": "Buzzer test tone triggered in background thread.",
    }
