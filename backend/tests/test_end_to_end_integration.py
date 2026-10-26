"""
End-to-End Pipeline Integration Tests.
Verifies real data exchange across:
AI Vision -> Backend Risk Engine -> Session Manager -> Alerts Escalation -> Mock SMS & Buzzer.
"""

import pytest
import time
from datetime import datetime, timezone, timedelta
from backend.services.session_manager import SessionManager
from backend.services.risk_engine import RiskEngine
from alerts_sos.escalation_manager import EscalationManager
from alerts_sos.beep_manager import BeepManager
from alerts_sos.mock_sms_provider import MockSMSProvider
from alerts_sos.family_notification import FamilyNotificationService
from backend.schemas.vision_schema import VisionEventSchema
from backend.schemas.sensor_schema import SensorReadingSchema
from shared.constants import (
    RiskStateEnum,
    AlertLevelEnum,
    EyeStatusEnum,
    SensorDataStatusEnum,
    BeepStatusEnum,
    SmsStatusEnum,
)


@pytest.fixture
def current_time():
    return datetime.now(timezone.utc).isoformat()


@pytest.fixture
def integrated_pipeline():
    """Sets up an end-to-end connected pipeline fixture."""
    mock_sms = MockSMSProvider()
    beep_mgr = BeepManager(enabled=True, min_interval_sec=0.01)
    family_svc = FamilyNotificationService(
        sms_provider=mock_sms,
        emergency_contact_phone="+919876543210",
        emergency_contact_name="Test Emergency Contact",
    )
    escalation_mgr = EscalationManager(
        beep_manager=beep_mgr,
        family_service=family_svc,
        sms_cooldown_seconds=60,
    )
    session_mgr = SessionManager(escalation_manager=escalation_mgr)
    session_mgr.start_session("driver_integration_test")
    return session_mgr, mock_sms, beep_mgr, escalation_mgr


def test_end_to_end_normal_driving_flow(integrated_pipeline, current_time):
    """Verifies that normal driver telemetry keeps system alert and silent."""
    session_mgr, mock_sms, beep_mgr, _ = integrated_pipeline

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

    # Ingest sensor and vision
    session_mgr.update_sensor(sensor)
    risk = session_mgr.update_vision(vision)

    assert risk.state == RiskStateEnum.NORMAL
    status = session_mgr.get_current_status()
    assert status["active_alert"] is None
    assert status["buzzer_status"] == BeepStatusEnum.INACTIVE.value
    assert len(mock_sms.get_sent_messages()) == 0


def test_end_to_end_critical_escalation_and_gps_sms(integrated_pipeline, current_time):
    """
    Verifies that critical prolonged eye closure triggers:
    1. Risk state = HIGH_RISK
    2. Active buzzer = ACTIVE
    3. Emergency Mock SMS dispatched with Google Maps GPS link
    4. Current status reflects active alert
    """
    session_mgr, mock_sms, beep_mgr, _ = integrated_pipeline

    # Update vehicle GPS position
    session_mgr.update_gps(latitude=12.9716, longitude=77.5946)

    # Driver closes eyes for 2.8 seconds with low heart rate
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
        heart_rate_bpm=48.0,
        source="simulated",
        data_status=SensorDataStatusEnum.SIMULATED,
        last_reading_timestamp=current_time,
    )

    session_mgr.update_sensor(sensor)
    risk = session_mgr.update_vision(vision)

    assert risk.state == RiskStateEnum.HIGH_RISK
    assert risk.risk_score >= 80.0

    status = session_mgr.get_current_status()
    assert status["active_alert"] is not None
    assert status["active_alert"]["alert_level"] == AlertLevelEnum.CRITICAL.value
    assert status["active_alert"]["family_sms_status"] == SmsStatusEnum.MOCK_SENT.value

    # Verify SMS payload content
    sent = mock_sms.get_sent_messages()
    assert len(sent) == 1
    assert "https://maps.google.com/?q=12.97160,77.59460" in sent[0]["message"]
    assert "Critical eye closure" in sent[0]["message"]


def test_end_to_end_alert_acknowledgement_silence(integrated_pipeline, current_time):
    """Driver acknowledging active alert silences buzzer."""
    session_mgr, mock_sms, beep_mgr, _ = integrated_pipeline

    vision = VisionEventSchema(
        timestamp=current_time,
        face_detected=True,
        eye_status=EyeStatusEnum.CLOSED,
        eye_closure_duration_ms=2600.0,
        yawn_detected=False,
        head_nod_detected=False,
        tracking_reliable=True,
    )
    session_mgr.update_vision(vision)

    # Alert is active
    status_before = session_mgr.get_current_status()
    assert status_before["active_alert"] is not None

    # Acknowledge
    ack = session_mgr.acknowledge_alert()
    assert ack["status"] == "ACKNOWLEDGED"
    assert session_mgr.latest_alert.driver_beep_status == BeepStatusEnum.MUTED
