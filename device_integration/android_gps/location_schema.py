"""
GPS Location Schema.
Data contract for Android smartphone GPS telemetry bridge.
Supports live satellite fixes, browser Geolocation API, mobile webhooks,
and clear error / permission states.
"""

from typing import Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field, model_validator
from shared.constants import GpsFreshnessEnum, GpsPermissionEnum

# Maximum seconds before a GPS fix is deemed STALE (default: 30s)
GPS_STALENESS_THRESHOLD_SECONDS = 30.0


class GPSLocationSchema(BaseModel):
    """Payload representing geographic coordinate sample from phone GPS bridge."""

    timestamp: str = Field(
        ...,
        description="ISO-8601 UTC timestamp of location fix.",
        examples=["2026-10-26T12:00:00.000Z"],
    )
    latitude: Optional[float] = Field(
        default=None,
        ge=-90.0,
        le=90.0,
        description="WGS84 latitude coordinate. None if permission denied or unavailable.",
        examples=[12.9716],
    )
    longitude: Optional[float] = Field(
        default=None,
        ge=-180.0,
        le=180.0,
        description="WGS84 longitude coordinate. None if permission denied or unavailable.",
        examples=[77.5946],
    )
    altitude_m: Optional[float] = Field(
        default=None,
        description="Altitude in meters above sea level.",
    )
    speed_kmh: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Ground speed in kilometers per hour.",
    )
    accuracy_m: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Horizontal GPS accuracy radius in meters.",
    )
    source: str = Field(
        default="android_gps_bridge",
        description="Identifier of bridge mechanism (e.g. 'android_browser_gps', 'android_http_webhook', 'simulated_gps').",
    )
    permission_status: GpsPermissionEnum = Field(
        default=GpsPermissionEnum.GRANTED,
        description="GPS sensor permission state (GRANTED, DENIED, PROMPT, UNAVAILABLE, NOT_REQUESTED).",
    )
    freshness_status: GpsFreshnessEnum = Field(
        default=GpsFreshnessEnum.LIVE,
        description="Freshness flag (LIVE, STALE, UNAVAILABLE, SIMULATED).",
    )
    is_valid: bool = Field(
        default=True,
        description="True if fix has adequate satellite lock and valid coordinates.",
    )
    error_state: Optional[str] = Field(
        default=None,
        description="Detailed error reason if location unavailable or permission denied.",
    )

    @model_validator(mode="after")
    def validate_gps_integrity(self):
        """Validate coordinate presence and determine freshness."""
        if self.permission_status == GpsPermissionEnum.DENIED:
            self.is_valid = False
            self.freshness_status = GpsFreshnessEnum.UNAVAILABLE
            if not self.error_state:
                self.error_state = "Location permission denied by user or Android system."

        if self.latitude is None or self.longitude is None:
            self.is_valid = False
            if self.permission_status != GpsPermissionEnum.DENIED:
                self.freshness_status = GpsFreshnessEnum.UNAVAILABLE
        else:
            # Check staleness if not simulated
            if self.source == "simulated_gps":
                self.freshness_status = GpsFreshnessEnum.SIMULATED
            else:
                try:
                    ts_str = self.timestamp.replace("Z", "+00:00")
                    dt = datetime.fromisoformat(ts_str)
                    age_seconds = (datetime.now(timezone.utc) - dt).total_seconds()
                    if age_seconds > GPS_STALENESS_THRESHOLD_SECONDS:
                        self.freshness_status = GpsFreshnessEnum.STALE
                        if not self.error_state:
                            self.error_state = f"GPS fix is stale ({age_seconds:.0f}s old)."
                except Exception:
                    pass
        return self

    model_config = {
        "extra": "forbid",
        "json_schema_extra": {
            "example": {
                "timestamp": "2026-10-26T12:00:00.000Z",
                "latitude": 12.9716,
                "longitude": 77.5946,
                "altitude_m": 920.0,
                "speed_kmh": 45.5,
                "accuracy_m": 4.2,
                "source": "android_http_webhook",
                "permission_status": "GRANTED",
                "freshness_status": "LIVE",
                "is_valid": True,
            }
        },
    }
