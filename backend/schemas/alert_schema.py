"""
Pydantic data models for alerts and SOS notifications.
Conforms strictly to shared/schemas/alert_event.schema.json.
"""

from typing import Optional
from pydantic import BaseModel, Field
from shared.constants import (
    AlertLevelEnum,
    BeepStatusEnum,
    SmsStatusEnum,
    LocationStatusEnum,
)


class AlertEventSchema(BaseModel):
    """Payload representing an alert or emergency action triggered by the system."""

    event_id: str = Field(
        ...,
        description="Unique identifier (e.g. UUID) for this alert instance.",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    timestamp: str = Field(
        ...,
        description="ISO-8601 UTC timestamp when alert was triggered.",
    )
    alert_level: AlertLevelEnum = Field(
        ...,
        description="Severity level of the incident.",
    )
    reason: str = Field(
        ...,
        description="Human-readable explanation of why this alert fired.",
        examples=["Prolonged eye closure detected (2.8s) with heart rate dip."],
    )
    driver_beep_status: BeepStatusEnum = Field(
        ...,
        description="Status of cabin acoustic buzzer.",
    )
    family_sms_status: SmsStatusEnum = Field(
        ...,
        description="Status of emergency SMS dispatch to family contact.",
    )
    location_status: LocationStatusEnum = Field(
        ...,
        description="Availability status of GPS coordinates at alert time.",
    )
    latitude: Optional[float] = Field(
        default=None,
        ge=-90.0,
        le=90.0,
        description="Vehicle latitude if GPS was available.",
    )
    longitude: Optional[float] = Field(
        default=None,
        ge=-180.0,
        le=180.0,
        description="Vehicle longitude if GPS was available.",
    )

    model_config = {
        "extra": "forbid",
        "json_schema_extra": {
            "example": {
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2026-10-26T12:00:00.000Z",
                "alert_level": "CRITICAL",
                "reason": "Eyes closed for > 2.5 seconds with low heart rate",
                "driver_beep_status": "ACTIVE",
                "family_sms_status": "MOCK_SENT",
                "location_status": "AVAILABLE",
                "latitude": 12.9716,
                "longitude": 77.5946,
            }
        },
    }
