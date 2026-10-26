"""
Alerts & SOS Package.
Audible warnings, risk escalation, and emergency family notifications.
"""

import os
from typing import Optional
from alerts_sos.beep_manager import BeepManager
from alerts_sos.sms_provider import BaseSMSProvider
from alerts_sos.mock_sms_provider import MockSMSProvider
from alerts_sos.real_sms_provider import TwilioSMSProvider, Fast2SMSProvider
from alerts_sos.family_notification import FamilyNotificationService
from alerts_sos.escalation_manager import EscalationManager


def get_sms_provider(provider_name: Optional[str] = None) -> BaseSMSProvider:
    """Factory creating configured SMS provider, defaulting to MockSMSProvider for safety."""
    p_name = (provider_name or os.getenv("SMS_PROVIDER", "mock")).lower().strip()
    if p_name == "twilio":
        twilio_prov = TwilioSMSProvider()
        if twilio_prov.is_configured:
            return twilio_prov
    elif p_name == "fast2sms":
        f2s = Fast2SMSProvider()
        if f2s.is_configured:
            return f2s
    return MockSMSProvider()


# Global default instances configured for development and testing
default_beep_manager = BeepManager(enabled=True, min_interval_sec=1.0)
default_sms_provider = get_sms_provider()
default_family_service = FamilyNotificationService(
    sms_provider=default_sms_provider,
    emergency_contact_phone=os.getenv("EMERGENCY_CONTACT_PHONE", "+919876543210"),
    emergency_contact_name=os.getenv("EMERGENCY_CONTACT_NAME", "Family Emergency Contact"),
)
default_escalation_manager = EscalationManager(
    beep_manager=default_beep_manager,
    family_service=default_family_service,
    sms_cooldown_seconds=int(os.getenv("ALERT_SMS_COOLDOWN_SECONDS", "120")),
    ack_window_seconds=float(os.getenv("ALERT_ACK_WINDOW_SECONDS", "0.0")),
)

__all__ = [
    "BeepManager",
    "BaseSMSProvider",
    "MockSMSProvider",
    "TwilioSMSProvider",
    "Fast2SMSProvider",
    "FamilyNotificationService",
    "EscalationManager",
    "get_sms_provider",
    "default_beep_manager",
    "default_sms_provider",
    "default_family_service",
    "default_escalation_manager",
]
