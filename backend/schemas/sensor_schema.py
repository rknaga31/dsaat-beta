"""
Pydantic data models for smartwatch physiological and biometric readings.
Conforms strictly to shared/schemas/sensor_reading.schema.json.
"""

from typing import Optional, Any
from pydantic import BaseModel, Field, model_validator
from shared.constants import SensorDataStatusEnum


class SensorReadingSchema(BaseModel):
    """Payload representing a biometric sample from a smartwatch or simulated stream."""

    timestamp: str = Field(
        ...,
        description="ISO-8601 UTC timestamp of biometric capture.",
        examples=["2026-10-26T12:00:00.000Z"],
    )
    heart_rate_bpm: Optional[float] = Field(
        default=None,
        description="Heart rate in beats per minute. None if unavailable. NEVER 0.",
    )
    source: str = Field(
        ...,
        description="Device identifier or adapter source name (e.g. 'boult_ble', 'simulated').",
    )
    data_status: SensorDataStatusEnum = Field(
        ...,
        description="Status flag indicating integrity (LIVE, SIMULATED, UNAVAILABLE, STALE).",
    )
    last_reading_timestamp: Optional[str] = Field(
        default=None,
        description="Timestamp of last verified reading or None if never connected.",
    )
    device_battery_percent: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Reported battery percentage if supported.",
    )
    connection_status: bool = Field(
        default=False,
        description="Indicates whether the sensor device or adapter is actively connected.",
    )
    data_freshness_seconds: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Elapsed seconds since biometric reading was sampled.",
    )
    error_state: Optional[str] = Field(
        default=None,
        description="Detailed diagnostic or error message if sensor is degraded or unavailable.",
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            status = data.get("data_status")
            if status == "SIMULATED":
                data["data_status"] = "SIMULATED_DEMO"
            elif status == "STALE":
                data["data_status"] = "STALE_DATA"
            elif status == "LIVE":
                data["data_status"] = "CONNECTED_LIVE"
        return data

    @model_validator(mode="after")
    def validate_reading_integrity(self):
        """Enforce strict integrity rules across biometric samples."""
        if self.heart_rate_bpm is not None:
            if self.heart_rate_bpm <= 0:
                raise ValueError(
                    "Invalid heart_rate_bpm. Heart rate cannot be 0 or negative; "
                    "use None (null) to represent unavailable sensor telemetry."
                )
            if self.heart_rate_bpm < 30.0 or self.heart_rate_bpm > 240.0:
                raise ValueError(
                    f"Invalid heart_rate_bpm ({self.heart_rate_bpm}). "
                    "Heart rate must be within physiological boundary limits [30.0, 240.0] BPM."
                )
        if self.source == "simulated" and self.data_status in (
            SensorDataStatusEnum.LIVE,
            SensorDataStatusEnum.CONNECTED_LIVE,
        ):
            raise ValueError("Simulated data streams MUST NOT be marked as LIVE / CONNECTED_LIVE.")
        return self

    model_config = {
        "extra": "forbid",
        "json_schema_extra": {
            "example": {
                "timestamp": "2026-10-26T12:00:00.000Z",
                "heart_rate_bpm": 74.0,
                "source": "simulated",
                "data_status": "SIMULATED",
                "last_reading_timestamp": "2026-10-26T12:00:00.000Z",
                "device_battery_percent": 88.0,
            }
        },
    }
