"""
Unit tests for Alerts & SOS Escalation Manager and Notification Services.
"""

import pytest
from datetime import datetime, timezone
from backend.schemas.risk_schema import RiskStateSchema
from alerts_sos.beep_manager import BeepManager
from alerts_sos.mock_sms_provider import MockSMSProvider
from alerts_sos.family_notification import FamilyNotificationService
from alerts_sos.escalation_manager import EscalationManager
from shared.constants import (
    RiskStateEnum,
    AlertLevelEnum,
    SmsStatusEnum,
    BeepStatusEnum,
)


@pytest.fixture
def current_time():
    return datetime.now(timezone.utc).isoformat()


@pytest.fixture
def escalation_setup():
    mock_provider = MockSMSProvider()
    beep_mgr = BeepManager(enabled=True, min_interval_sec=0.1)
    family_svc = FamilyNotificationService(
        sms_provider=mock_provider,
        emergency_contact_phone="+919876543210",
        emergency_contact_name="Family Contact",
    )
    escalation_mgr = EscalationManager(
        beep_manager=beep_mgr,
        family_service=family_svc,
        sms_cooldown_seconds=60,
    )
    return escalation_mgr, mock_provider, beep_mgr


def test_normal_risk_no_alert(escalation_setup, current_time):
    escalation_mgr, mock_provider, beep_mgr = escalation_setup
    risk = RiskStateSchema(
        timestamp=current_time,
        state=RiskStateEnum.NORMAL,
        risk_score=10.0,
        contributing_reasons=["Driver alert"],
        monitoring_reliable=True,
    )
    alert = escalation_mgr.process_risk_update(risk)
    assert alert is None
    assert len(mock_provider.get_sent_messages()) == 0


def test_warning_risk_triggers_beep_only(escalation_setup, current_time):
    escalation_mgr, mock_provider, beep_mgr = escalation_setup
    risk = RiskStateSchema(
        timestamp=current_time,
        state=RiskStateEnum.WARNING,
        risk_score=55.0,
        contributing_reasons=["Prolonged eye closure (1.8s)"],
        monitoring_reliable=True,
    )
    alert = escalation_mgr.process_risk_update(risk)
    assert alert is not None
    assert alert.alert_level == AlertLevelEnum.WARNING
    assert alert.family_sms_status == SmsStatusEnum.NOT_TRIGGERED
    assert len(mock_provider.get_sent_messages()) == 0


def test_high_risk_triggers_beep_and_mock_sms(escalation_setup, current_time):
    escalation_mgr, mock_provider, beep_mgr = escalation_setup
    risk = RiskStateSchema(
        timestamp=current_time,
        state=RiskStateEnum.HIGH_RISK,
        risk_score=90.0,
        contributing_reasons=["Critical eye closure (2.8s)"],
        monitoring_reliable=True,
    )
    alert = escalation_mgr.process_risk_update(risk, latitude=12.9716, longitude=77.5946)
    assert alert is not None
    assert alert.alert_level == AlertLevelEnum.CRITICAL
    assert alert.family_sms_status == SmsStatusEnum.MOCK_SENT
    assert len(mock_provider.get_sent_messages()) == 1

    sent_msg = mock_provider.get_sent_messages()[0]["message"]
    assert "https://maps.google.com/?q=12.97160,77.59460" in sent_msg


def test_duplicate_sms_cooldown_prevention(escalation_setup, current_time):
    """A second HIGH_RISK event immediately following the first must NOT trigger a second SMS."""
    escalation_mgr, mock_provider, beep_mgr = escalation_setup
    risk = RiskStateSchema(
        timestamp=current_time,
        state=RiskStateEnum.HIGH_RISK,
        risk_score=95.0,
        contributing_reasons=["Eyes closed"],
        monitoring_reliable=True,
    )

    # First trigger: sends SMS
    alert1 = escalation_mgr.process_risk_update(risk)
    assert alert1.family_sms_status == SmsStatusEnum.MOCK_SENT
    assert len(mock_provider.get_sent_messages()) == 1

    # Second trigger immediately: cooldown prevents duplicate
    alert2 = escalation_mgr.process_risk_update(risk)
    assert alert2.family_sms_status == SmsStatusEnum.NOT_TRIGGERED
    assert len(mock_provider.get_sent_messages()) == 1
