"""
Pydantic data models for fused multimodal risk assessment states.
Conforms strictly to shared/schemas/risk_state.schema.json.
"""

from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from shared.constants import RiskStateEnum


class RiskStateSchema(BaseModel):
    """Payload representing current overall driver risk assessment."""

    timestamp: str = Field(
        ...,
        description="ISO-8601 UTC timestamp of risk calculation.",
        examples=["2026-10-26T12:00:00.000Z"],
    )
    state: RiskStateEnum = Field(
        ...,
        description="Risk classification tier.",
    )
    risk_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Composite normalized risk score from 0.0 (safest) to 100.0 (maximum risk).",
    )
    contributing_reasons: List[str] = Field(
        default_factory=list,
        description="Deterministic list of reasons driving the current score and state.",
    )
    monitoring_reliable: bool = Field(
        ...,
        description="Flag indicating if real-time inputs were trustworthy enough to calculate valid risk.",
    )
    vision_snapshot: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional snapshot of vision event evaluated during this step.",
    )
    sensor_snapshot: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional snapshot of sensor reading evaluated during this step.",
    )

    model_config = {
        "extra": "forbid",
        "json_schema_extra": {
            "example": {
                "timestamp": "2026-10-26T12:00:00.000Z",
                "state": "NORMAL",
                "risk_score": 12.5,
                "contributing_reasons": ["Driver alert and eyes open", "Normal resting heart rate"],
                "monitoring_reliable": True,
            }
        },
    }
