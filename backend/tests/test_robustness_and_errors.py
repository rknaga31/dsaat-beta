"""
Robustness, Error Handling, and Boundary Condition Tests.
Verifies sensor freshness validation, missing-face distraction timeouts,
GPS unavailability fallbacks, SMS error recovery, and camera reconnection logic.
"""

import pytest
import time
from datetime import datetime, timezone, timedelta
from backend.services.risk_engine import RiskEngine
from backend.schemas.vision_schema import VisionEventSchema
from backend.schemas.sensor_schema import SensorReadingSchema
from shared.constants import (
    RiskStateEnum,
    EyeStatusEnum,
    SensorDataStatusEnum,
    SmsStatusEnum,
    LocationStatusEnum,
)
from alerts_sos.family_notification import FamilyNotificationService
from alerts_sos.sms_provider import BaseSMSProvider
from ai_vision.camera_manager import CameraManager


def test_sensor_staleness_detection():
    """Readings older than 10 seconds must be flagged STALE and excluded from risk calculation."""
    engine = RiskEngine(max_sensor_staleness_sec=10.0)

    # Reading from 30 seconds ago
    old_time = (datetime.now(timezone.utc) - timedelta(seconds=30)).isoformat()
    current_time = datetime.now(timezone.utc).isoformat()

    stale_sensor = SensorReadingSchema(
        timestamp=old_time,
        heart_rate_bpm=45.0,  # Bradycardia reading, but it is stale!
        source="simulated",
        data_status=SensorDataStatusEnum.SIMULATED,
        last_reading_timestamp=old_time,
    )

    # Driver eyes open
    vision = VisionEventSchema(
        timestamp=current_time,
        face_detected=True,
        eye_status=EyeStatusEnum.OPEN,
        eye_closure_duration_ms=0.0,
        yawn_detected=False,
        head_nod_detected=False,
        tracking_reliable=True,
    )

    result = engine.evaluate_risk(vision_event=vision, sensor_reading=stale_sensor)

    # Sensor status should be updated to STALE
    assert stale_sensor.data_status == SensorDataStatusEnum.STALE
    # Because old HR is ignored, state should remain NORMAL based on open eyes
    assert result.state == RiskStateEnum.NORMAL
    assert any("stale" in reason.lower() for reason in result.contributing_reasons)


def test_missing_face_distraction_timeout():
    """If face is not detected for > 3.0 seconds, risk engine must escalate to WARNING."""
    engine = RiskEngine(face_lost_threshold_ms=100.0)  # low threshold for test speed
    current_time = datetime.now(timezone.utc).isoformat()

    no_face_vision = VisionEventSchema(
        timestamp=current_time,
        face_detected=False,
        eye_status=EyeStatusEnum.UNKNOWN,
        eye_closure_duration_ms=0.0,
        yawn_detected=False,
        head_nod_detected=False,
        tracking_reliable=False,
    )

    # First event: face missing starts tracking
    result1 = engine.evaluate_risk(vision_event=no_face_vision)
    assert result1.state == RiskStateEnum.MONITORING_UNAVAILABLE

    # Wait for threshold duration to elapse
    time.sleep(0.15)

    # Second event: face missing exceeds threshold -> triggers distraction WARNING
    result2 = engine.evaluate_risk(vision_event=no_face_vision)
    assert result2.state == RiskStateEnum.WARNING
    assert any("distraction" in r.lower() or "not visible" in r.lower() for r in result2.contributing_reasons)


def test_gps_unavailable_sms_fallback():
    """When GPS coordinates are None, SMS is formatted gracefully with 'GPS signal unavailable'."""
    class RecordingProvider(BaseSMSProvider):
        def __init__(self):
            self.last_msg = ""
        @property
        def provider_name(self):
            return "recording"
        def send_sms(self, recipient_phone: str, message_text: str) -> bool:
            self.last_msg = message_text
            return True

    provider = RecordingProvider()
    service = FamilyNotificationService(
        sms_provider=provider,
        emergency_contact_phone="+919876543210",
    )

    status, msg = service.dispatch_sos(
        driver_name="Test Driver",
        reason="Test Reason",
        latitude=None,
        longitude=None,
    )

    assert status == SmsStatusEnum.SENT
    assert "GPS signal unavailable" in msg
    assert "https://maps.google.com" not in msg


def test_sms_provider_exception_handling():
    """Provider raising unexpected network socket error must be caught gracefully without crashing."""
    class FaultyProvider(BaseSMSProvider):
        @property
        def provider_name(self):
            return "faulty"
        def send_sms(self, recipient_phone: str, message_text: str) -> bool:
            raise ConnectionResetError("Simulated remote network socket disconnect")

    service = FamilyNotificationService(
        sms_provider=FaultyProvider(),
        emergency_contact_phone="+919876543210",
    )

    # Must NOT raise exception; returns FAILED status cleanly
    status, msg = service.dispatch_sos(
        driver_name="Test Driver",
        reason="Critical eye closure",
        latitude=12.9716,
        longitude=77.5946,
    )

    assert status == SmsStatusEnum.FAILED


def test_camera_manager_consecutive_failure_recovery():
    """CameraManager tracks read failures and triggers recovery attempts."""
    mgr = CameraManager(camera_index=999, max_failures_before_reconnect=3, reconnect_cooldown_sec=0.01)
    mgr.is_running = True
    mgr.cap = None  # Simulates broken handle

    # Read frame fails
    success, frame = mgr.read_frame()
    assert success is False
    assert frame is None
    assert mgr.consecutive_failures == 1

    # Second fail
    mgr.read_frame()
    assert mgr.consecutive_failures == 2

    # Third fail triggers recovery
    mgr.read_frame()
    assert mgr.consecutive_failures >= 3


def test_heart_rate_boundary_validation():
    """Pydantic model must reject physiologically invalid heart rates (< 30 bpm or > 240 bpm)."""
    current_time = datetime.now(timezone.utc).isoformat()

    # Valid boundary cases
    valid_lower = SensorReadingSchema(
        timestamp=current_time,
        heart_rate_bpm=30.0,
        source="simulated",
        data_status=SensorDataStatusEnum.SIMULATED,
        last_reading_timestamp=current_time,
    )
    assert valid_lower.heart_rate_bpm == 30.0

    valid_upper = SensorReadingSchema(
        timestamp=current_time,
        heart_rate_bpm=240.0,
        source="simulated",
        data_status=SensorDataStatusEnum.SIMULATED,
        last_reading_timestamp=current_time,
    )
    assert valid_upper.heart_rate_bpm == 240.0

    # Invalid: 25 bpm (< 30)
    with pytest.raises(ValueError):
        SensorReadingSchema(
            timestamp=current_time,
            heart_rate_bpm=25.0,
            source="simulated",
            data_status=SensorDataStatusEnum.SIMULATED,
            last_reading_timestamp=current_time,
        )

    # Invalid: 250 bpm (> 240)
    with pytest.raises(ValueError):
        SensorReadingSchema(
            timestamp=current_time,
            heart_rate_bpm=250.0,
            source="simulated",
            data_status=SensorDataStatusEnum.SIMULATED,
            last_reading_timestamp=current_time,
        )
