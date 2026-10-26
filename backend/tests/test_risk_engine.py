"""
Unit tests for Backend Risk Engine Service.
Tests multimodal fusion, threshold escalation, and edge case telemetry handling.
"""

import pytest
from datetime import datetime, timezone
from backend.services.risk_engine import RiskEngine
from backend.schemas.vision_schema import VisionEventSchema
from backend.schemas.sensor_schema import SensorReadingSchema
from shared.constants import RiskStateEnum, EyeStatusEnum, SensorDataStatusEnum


@pytest.fixture
def engine():
    return RiskEngine()


@pytest.fixture
def current_time():
    return datetime.now(timezone.utc).isoformat()


def test_monitoring_unavailable_when_no_inputs(engine):
    """If neither vision nor sensor data is provided, state must be MONITORING_UNAVAILABLE."""
    result = engine.evaluate_risk(vision_event=None, sensor_reading=None)
    assert result.state == RiskStateEnum.MONITORING_UNAVAILABLE
    assert result.monitoring_reliable is False
    assert result.risk_score == 0.0


def test_monitoring_unavailable_when_tracking_unreliable(engine, current_time):
    """If face is not detected or tracking is unreliable, monitoring is flagged as unreliable."""
    vision = VisionEventSchema(
        timestamp=current_time,
        face_detected=False,
        eye_status=EyeStatusEnum.UNKNOWN,
        eye_closure_duration_ms=0.0,
        yawn_detected=False,
        head_nod_detected=False,
        tracking_reliable=False,
    )
    result = engine.evaluate_risk(vision_event=vision, sensor_reading=None)
    assert result.state == RiskStateEnum.MONITORING_UNAVAILABLE
    assert result.monitoring_reliable is False


def test_normal_alert_state(engine, current_time):
    """Driver with open eyes and normal heart rate should evaluate to NORMAL risk state."""
    vision = VisionEventSchema(
        timestamp=current_time,
        face_detected=True,
        eye_status=EyeStatusEnum.OPEN,
        eye_closure_duration_ms=0.0,
        yawn_detected=False,
        head_nod_detected=False,
        tracking_reliable=True,
    )
    sensor = SensorReadingSchema(
        timestamp=current_time,
        heart_rate_bpm=72.0,
        source="simulated",
        data_status=SensorDataStatusEnum.SIMULATED,
        last_reading_timestamp=current_time,
    )
    result = engine.evaluate_risk(vision_event=vision, sensor_reading=sensor)
    assert result.state == RiskStateEnum.NORMAL
    assert result.risk_score < 40.0
    assert result.monitoring_reliable is True


def test_warning_state_on_moderate_eye_closure_and_yawn(engine, current_time):
    """Eyes closed for 1.8s + yawn should elevate risk to WARNING."""
    vision = VisionEventSchema(
        timestamp=current_time,
        face_detected=True,
        eye_status=EyeStatusEnum.CLOSED,
        eye_closure_duration_ms=1800.0,
        yawn_detected=True,
        head_nod_detected=False,
        tracking_reliable=True,
    )
    result = engine.evaluate_risk(vision_event=vision, sensor_reading=None)
    assert result.state == RiskStateEnum.WARNING
    assert result.risk_score >= 40.0
    assert result.monitoring_reliable is True


def test_high_risk_state_on_critical_eye_closure(engine, current_time):
    """Eyes closed for >= 2.5s should evaluate to HIGH_RISK."""
    vision = VisionEventSchema(
        timestamp=current_time,
        face_detected=True,
        eye_status=EyeStatusEnum.CLOSED,
        eye_closure_duration_ms=2800.0,
        yawn_detected=False,
        head_nod_detected=True,
        tracking_reliable=True,
    )
    sensor = SensorReadingSchema(
        timestamp=current_time,
        heart_rate_bpm=48.0,  # Low heart rate exacerbates drowsiness
        source="simulated",
        data_status=SensorDataStatusEnum.SIMULATED,
        last_reading_timestamp=current_time,
    )
    result = engine.evaluate_risk(vision_event=vision, sensor_reading=sensor)
    assert result.state == RiskStateEnum.HIGH_RISK
    assert result.risk_score >= 80.0
    assert any("Critical eye closure" in r for r in result.contributing_reasons)


def test_reject_zero_heart_rate(current_time):
    """Enforce data contract rule: heart_rate_bpm must never be 0."""
    with pytest.raises(ValueError):
        SensorReadingSchema(
            timestamp=current_time,
            heart_rate_bpm=0.0,  # Must be rejected!
            source="simulated",
            data_status=SensorDataStatusEnum.SIMULATED,
            last_reading_timestamp=current_time,
        )
