"""
Pydantic data models for computer vision events.
Conforms strictly to shared/schemas/vision_event.schema.json.
"""

from typing import Optional
from pydantic import BaseModel, Field
from shared.constants import EyeStatusEnum


class VisionEventSchema(BaseModel):
    """Payload representing one frame or processed window of facial analysis."""

    timestamp: str = Field(
        ...,
        description="ISO-8601 formatted timestamp of frame capture.",
        examples=["2026-10-26T12:00:00.000Z"],
    )
    face_detected: bool = Field(
        ...,
        description="True if primary driver face was localized.",
    )
    eye_status: EyeStatusEnum = Field(
        ...,
        description="Assessed eye closure state.",
    )
    eye_closure_duration_ms: float = Field(
        ...,
        ge=0.0,
        description="Continuous duration in milliseconds of eye closure.",
    )
    yawn_detected: bool = Field(
        ...,
        description="True if sustained yawning mouth pattern was detected.",
    )
    head_nod_detected: bool = Field(
        ...,
        description="True if drowsy head pitch nodding motion was detected.",
    )
    tracking_reliable: bool = Field(
        ...,
        description="True if lighting and facial landmark tracking are confident.",
    )
    ear_score: Optional[float] = Field(
        default=None,
        description="Optional Eye Aspect Ratio calculation.",
    )
    mar_score: Optional[float] = Field(
        default=None,
        description="Optional Mouth Aspect Ratio calculation.",
    )

    model_config = {
        "extra": "forbid",
        "json_schema_extra": {
            "example": {
                "timestamp": "2026-10-26T12:00:00.000Z",
                "face_detected": True,
                "eye_status": "OPEN",
                "eye_closure_duration_ms": 0.0,
                "yawn_detected": False,
                "head_nod_detected": False,
                "tracking_reliable": True,
                "ear_score": 0.32,
                "mar_score": 0.15,
            }
        },
    }
