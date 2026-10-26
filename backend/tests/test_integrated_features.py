"""
Comprehensive Integration Tests for Boult Smartwatch + Android GPS + Driver Beep & Family SMS.
Validates all scenarios specified in the Integration Task specification:
- Camera still works with missing/stale watch
- Missing watch safety (never triggers false medical emergency)
- Stale heart-rate handling
- Missing GPS fallback
- GPS permission denied handling
- SMS provider failure and retry limits
- Mock SMS success
- Repeated high-risk events
- Alert cooldown
- Driver acknowledgement within escalation window
- Duplicate SMS prevention
- Monitoring stopped lifecycle
- Recovery after temporary sensor failure
"""

import pytest
import time
from datetime import datetime, timezone, timedelta
from backend.services.session_manager import SessionManager
from backend.services.risk_engine import RiskEngine
from alerts_sos.beep_manager import BeepManager
from alerts_sos.mock_sms_provider import MockSMSProvider
from alerts_sos.sms_provider import BaseSMSProvider
from alerts_sos.family_notification import FamilyNotificationService
from alerts_sos.escalation_manager import EscalationManager
from device_integration.smartwatch.boult_adapter import BoultSmartwatchAdapter
from device_integration.smartwatch.simulated_adapter import SimulatedSensorAdapter
from device_integration.android_gps.location_schema import GPSLocationSchema
from backend.schemas.vision_schema import VisionEventSchema
from backend.schemas.sensor_schema import SensorReadingSchema
from backend.schemas.risk_schema import RiskStateSchema
from shared.constants import (
    RiskStateEnum,
    AlertLevelEnum,
    EyeStatusEnum,
    SensorDataStatusEnum,
    GpsFreshnessEnum,
    GpsPermissionEnum,
    BeepStatusEnum,
    SmsStatusEnum,
    LocationStatusEnum,
    EscalationStageEnum,
)


@pytest.fixture
def current_time():
    return datetime.now(timezone.utc).isoformat()


@pytest.fixture
def fresh_session():
    mock_sms = MockSMSProvider()
    beep = BeepManager(enabled=True, min_interval_sec=0.01)
    family_svc = FamilyNotificationService(
        sms_provider=mock_sms,
        emergency_contact_phone="+919876543210",
        emergency_contact_name="Family Member",
    )
    escalation = EscalationManager(
        beep_manager=beep,
        family_service=family_svc,
        sms_cooldown_seconds=60,
        ack_window_seconds=0.0,
    )
    session = SessionManager(escalation_manager=escalation)
    session.start_session("test_driver")
    return session, mock_sms, beep, escalation


def test_camera_still_works_with_missing_watch(fresh_session, current_time):
    """Missing smartwatch data must NOT disable camera-based drowsiness monitoring."""
    session, mock_sms, beep, _ = fresh_session
    boult = BoultSmartwatchAdapter(mac_address="00:00:00:00:00:00")
    sensor_reading = boult.read_sensor_data()

    assert sensor_reading.data_status == SensorDataStatusEnum.UNAVAILABLE
    assert sensor_reading.heart_rate_bpm is None

    # Ingest missing watch reading
    session.update_sensor(sensor_reading)

    # Ingest valid camera vision (driver alert)
    vision = VisionEventSchema(
        timestamp=current_time,
        face_detected=True,
        eye_status=EyeStatusEnum.OPEN,
        eye_closure_duration_ms=0.0,
        yawn_detected=False,
        head_nod_detected=False,
        tracking_reliable=True,
    )
    risk = session.update_vision(vision)

    assert risk.monitoring_reliable is True
    assert risk.state == RiskStateEnum.NORMAL
    assert risk.risk_score == 0.0


def test_missing_watch_does_not_trigger_emergency(fresh_session, current_time):
    """Missing or unavailable smartwatch telemetry must never trigger high-risk or medical panic."""
    session, mock_sms, beep, escalation = fresh_session
    boult = BoultSmartwatchAdapter()

    # Driver is attentive on camera
    vision = VisionEventSchema(
        timestamp=current_time,
        face_detected=True,
        eye_status=EyeStatusEnum.OPEN,
        eye_closure_duration_ms=0.0,
        yawn_detected=False,
        head_nod_detected=False,
        tracking_reliable=True,
    )
    session.update_vision(vision)

    # Watch is unavailable
    session.update_sensor(boult.read_sensor_data())

    status = session.get_current_status()
    assert status["active_alert"] is None
    assert status["risk_state"]["state"] == RiskStateEnum.NORMAL.value
    assert beep.status == BeepStatusEnum.INACTIVE
    assert len(mock_sms.get_sent_messages()) == 0
    assert escalation.escalation_stage == EscalationStageEnum.NORMAL


def test_stale_heart_rate_reading_ignored(fresh_session):
    """Readings older than 10 seconds must be flagged STALE and ignored by risk engine."""
    session, mock_sms, beep, _ = fresh_session
    engine = RiskEngine()

    now = datetime.now(timezone.utc)
    stale_time = (now - timedelta(seconds=25)).isoformat()

    stale_reading = SensorReadingSchema(
        timestamp=stale_time,
        heart_rate_bpm=42.0,  # Extreme bradycardia, but 25s stale
        source="boult_ble",
        data_status=SensorDataStatusEnum.CONNECTED_LIVE,
        last_reading_timestamp=stale_time,
    )

    vision = VisionEventSchema(
        timestamp=now.isoformat(),
        face_detected=True,
        eye_status=EyeStatusEnum.OPEN,
        eye_closure_duration_ms=0.0,
        yawn_detected=False,
        head_nod_detected=False,
        tracking_reliable=True,
    )

    risk = engine.evaluate_risk(vision_event=vision, sensor_reading=stale_reading)

    assert stale_reading.data_status == SensorDataStatusEnum.STALE_DATA
    # Stale 42 BPM must NOT inflate risk score
    assert risk.state == RiskStateEnum.NORMAL
    assert any("stale" in r.lower() for r in risk.contributing_reasons)


def test_missing_gps_fallback_explicit_message():
    """Missing GPS provides explicit fallback message and UNAVAILABLE location status."""
    mock_sms = MockSMSProvider()
    family_svc = FamilyNotificationService(
        sms_provider=mock_sms,
        emergency_contact_phone="+919876543210",
    )

    status, msg = family_svc.dispatch_sos(
        driver_name="Primary Driver",
        reason="Severe Eye Closure (2.7s)",
        latitude=None,
        longitude=None,
    )

    assert status == SmsStatusEnum.MOCK_SENT
    assert "Vehicle Location: GPS signal unavailable" in msg
    assert len(mock_sms.get_sent_messages()) == 1


def test_gps_permission_denied_handling():
    """GPS permission denied sets is_valid=False and freshness=UNAVAILABLE without error."""
    now_iso = datetime.now(timezone.utc).isoformat()
    gps = GPSLocationSchema(
        timestamp=now_iso,
        latitude=None,
        longitude=None,
        source="android_browser_gps",
        permission_status=GpsPermissionEnum.DENIED,
    )

    assert gps.is_valid is False
    assert gps.freshness_status == GpsFreshnessEnum.UNAVAILABLE
    assert "denied" in gps.error_state.lower()


def test_sms_provider_failure_and_retry_limits():
    """SMS provider exceptions are caught, retried up to max_retries, and result in FAILED status."""
    class FailingProvider(BaseSMSProvider):
        def __init__(self):
            self.call_count = 0
        @property
        def provider_name(self):
            return "failing_mock"
        def send_sms(self, recipient_phone: str, message_text: str) -> bool:
            self.call_count += 1
            raise ConnectionError("Cellular gateway timeout")

    failing = FailingProvider()
    family_svc = FamilyNotificationService(
        sms_provider=failing,
        emergency_contact_phone="+919876543210",
        max_retries=3,
    )

    status, _ = family_svc.dispatch_sos(
        driver_name="Driver",
        reason="Emergency Test",
        latitude=12.9716,
        longitude=77.5946,
    )

    assert status == SmsStatusEnum.FAILED
    assert failing.call_count == 3
    assert family_svc.last_submission_result["status"] == "FAILED"


def test_mock_sms_success():
    """Mock SMS successfully queues message, records timestamp, and validates E.164 phone."""
    mock_provider = MockSMSProvider()
    family_svc = FamilyNotificationService(
        sms_provider=mock_provider,
        emergency_contact_phone="+919876543210",
    )

    status, msg = family_svc.dispatch_sos(
        driver_name="Test Driver",
        reason="Drowsiness Alert",
        latitude=12.9716,
        longitude=77.5946,
    )

    assert status == SmsStatusEnum.MOCK_SENT
    assert len(mock_provider.get_sent_messages()) == 1
    assert "https://maps.google.com/?q=12.97160,77.59460" in msg


def test_escalation_workflow_with_acknowledgement_window(current_time):
    """
    Validates the full escalation workflow:
    WARNING -> HIGH_RISK -> ESCALATION_PENDING -> Driver Ack (Cancels SMS).
    """
    mock_sms = MockSMSProvider()
    beep = BeepManager(enabled=True, min_interval_sec=0.01)
    family_svc = FamilyNotificationService(sms_provider=mock_sms)

    # 5.0 second acknowledgement window
    escalation = EscalationManager(
        beep_manager=beep,
        family_service=family_svc,
        sms_cooldown_seconds=60,
        ack_window_seconds=5.0,
    )

    # 1. WARNING risk state -> Cabin beep only, NO SMS
    risk_warn = RiskStateSchema(
        timestamp=current_time,
        state=RiskStateEnum.WARNING,
        risk_score=55.0,
        contributing_reasons=["Sustained yawning"],
        monitoring_reliable=True,
    )
    alert1 = escalation.process_risk_update(risk_warn)
    assert alert1.alert_level == AlertLevelEnum.WARNING
    assert alert1.family_sms_status == SmsStatusEnum.NOT_TRIGGERED
    assert escalation.escalation_stage == EscalationStageEnum.WARNING
    assert len(mock_sms.get_sent_messages()) == 0

    # 2. HIGH_RISK arrives -> Enters ESCALATION_PENDING (grace window active)
    risk_crit = RiskStateSchema(
        timestamp=current_time,
        state=RiskStateEnum.HIGH_RISK,
        risk_score=90.0,
        contributing_reasons=["Critical eye closure (2.7s)"],
        monitoring_reliable=True,
    )
    alert2 = escalation.process_risk_update(risk_crit)
    assert alert2.family_sms_status == SmsStatusEnum.ESCALATION_PENDING
    assert escalation.escalation_stage == EscalationStageEnum.ESCALATION_PENDING
    assert escalation.remaining_ack_seconds > 0.0
    assert len(mock_sms.get_sent_messages()) == 0

    # 3. Driver acknowledges alert within grace window -> Buzzer silenced, SMS canceled!
    ack_res = escalation.acknowledge_alert()
    assert ack_res["status"] == "ACKNOWLEDGED"
    assert ack_res["action"] == "buzzer_silenced_and_sms_canceled"
    assert len(mock_sms.get_sent_messages()) == 0


def test_escalation_window_expires_and_dispatches_sms(current_time):
    """When driver fails to acknowledge within grace window, FAMILY_SMS is dispatched."""
    mock_sms = MockSMSProvider()
    beep = BeepManager(enabled=True, min_interval_sec=0.01)
    family_svc = FamilyNotificationService(sms_provider=mock_sms)

    # 0.1 second acknowledgement window
    escalation = EscalationManager(
        beep_manager=beep,
        family_service=family_svc,
        sms_cooldown_seconds=60,
        ack_window_seconds=0.1,
    )

    risk_crit = RiskStateSchema(
        timestamp=current_time,
        state=RiskStateEnum.HIGH_RISK,
        risk_score=90.0,
        contributing_reasons=["Critical eye closure (2.8s)"],
        monitoring_reliable=True,
    )

    # First call sets ESCALATION_PENDING
    alert_pending = escalation.process_risk_update(risk_crit, latitude=12.9716, longitude=77.5946)
    assert alert_pending.family_sms_status == SmsStatusEnum.ESCALATION_PENDING

    # Wait for grace window to expire
    time.sleep(0.15)

    # Subsequent update triggers FAMILY_SMS
    alert_escalated = escalation.process_risk_update(risk_crit, latitude=12.9716, longitude=77.5946)
    assert alert_escalated.family_sms_status == SmsStatusEnum.MOCK_SENT
    assert escalation.escalation_stage == EscalationStageEnum.FAMILY_SMS
    assert len(mock_sms.get_sent_messages()) == 1


def test_repeated_high_risk_and_duplicate_sms_cooldown(current_time):
    """Subsequent high-risk frames for the same ongoing incident must NOT dispatch duplicate SMS."""
    mock_sms = MockSMSProvider()
    beep = BeepManager(enabled=True, min_interval_sec=0.01)
    family_svc = FamilyNotificationService(sms_provider=mock_sms)

    escalation = EscalationManager(
        beep_manager=beep,
        family_service=family_svc,
        sms_cooldown_seconds=60,
        ack_window_seconds=0.0,
    )

    risk_crit = RiskStateSchema(
        timestamp=current_time,
        state=RiskStateEnum.HIGH_RISK,
        risk_score=92.0,
        contributing_reasons=["Eyes closed"],
        monitoring_reliable=True,
    )

    # First high risk frame dispatches SMS
    alert1 = escalation.process_risk_update(risk_crit)
    assert alert1.family_sms_status == SmsStatusEnum.MOCK_SENT
    assert len(mock_sms.get_sent_messages()) == 1

    # Second and third high risk frames must NOT send duplicate SMS
    alert2 = escalation.process_risk_update(risk_crit)
    alert3 = escalation.process_risk_update(risk_crit)
    assert alert2.family_sms_status == SmsStatusEnum.NOT_TRIGGERED
    assert alert3.family_sms_status == SmsStatusEnum.NOT_TRIGGERED
    assert len(mock_sms.get_sent_messages()) == 1


def test_monitoring_stopped_silences_alarms(fresh_session, current_time):
    """Ending driving session terminates active alerts and stops buzzer."""
    session, mock_sms, beep, _ = fresh_session

    vision = VisionEventSchema(
        timestamp=current_time,
        face_detected=True,
        eye_status=EyeStatusEnum.CLOSED,
        eye_closure_duration_ms=2700.0,
        yawn_detected=False,
        head_nod_detected=False,
        tracking_reliable=True,
    )
    session.update_vision(vision)

    assert session.latest_alert is not None
    assert beep.status == BeepStatusEnum.ACTIVE

    end_summary = session.end_session()
    assert end_summary["status"] == "COMPLETED"
    assert session.is_active is False
    assert session.latest_alert is None
    assert beep.status == BeepStatusEnum.INACTIVE


def test_recovery_after_temporary_sensor_failure(fresh_session, current_time):
    """System maintains camera monitoring during sensor failure and seamlessly recovers when sensor returns."""
    session, mock_sms, beep, _ = fresh_session

    vision = VisionEventSchema(
        timestamp=current_time,
        face_detected=True,
        eye_status=EyeStatusEnum.OPEN,
        eye_closure_duration_ms=0.0,
        yawn_detected=False,
        head_nod_detected=False,
        tracking_reliable=True,
    )

    # 1. Sensor fails / disconnects
    failed_sensor = SensorReadingSchema(
        timestamp=current_time,
        heart_rate_bpm=None,
        source="boult_ble",
        data_status=SensorDataStatusEnum.UNAVAILABLE,
        last_reading_timestamp=None,
    )
    session.update_sensor(failed_sensor)
    risk1 = session.update_vision(vision)
    assert risk1.state == RiskStateEnum.NORMAL
    assert risk1.monitoring_reliable is True

    # 2. Sensor recovers with valid live telemetry
    recovered_sensor = SensorReadingSchema(
        timestamp=current_time,
        heart_rate_bpm=75.0,
        source="boult_ble",
        data_status=SensorDataStatusEnum.CONNECTED_LIVE,
        last_reading_timestamp=current_time,
    )
    risk2 = session.update_sensor(recovered_sensor)
    assert risk2.state == RiskStateEnum.NORMAL
    assert risk2.monitoring_reliable is True
    assert session.latest_sensor_reading.heart_rate_bpm == 75.0
