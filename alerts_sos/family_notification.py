"""
Family Notification Service.
Formats emergency SMS alerts with GPS location links and coordinates provider dispatch.
Adheres to honest medical safety: describes detected warning signs without claiming
a confirmed medical diagnosis.
Includes retry limits, submission tracking, and timestamped dispatch records.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Tuple, List, Dict, Any
from shared.constants import SmsStatusEnum, LocationStatusEnum
from alerts_sos.sms_provider import BaseSMSProvider

logger = logging.getLogger("family_notification")


class FamilyNotificationService:
    """Dispatches formatted SOS alerts to registered emergency contacts."""

    def __init__(
        self,
        sms_provider: BaseSMSProvider,
        emergency_contact_phone: str = "+910000000000",
        emergency_contact_name: str = "Emergency Contact",
        max_retries: int = 3,
    ):
        self.sms_provider = sms_provider
        self.emergency_contact_phone = emergency_contact_phone
        self.emergency_contact_name = emergency_contact_name
        self.max_retries = max_retries

        self.last_submission_result: Optional[Dict[str, Any]] = None
        self.dispatch_history: List[Dict[str, Any]] = []

    def update_contact(self, phone: str, name: Optional[str] = None) -> None:
        """Configures or updates the registered emergency contact."""
        self.emergency_contact_phone = phone
        if name:
            self.emergency_contact_name = name
        logger.info("Emergency contact updated to: %s (%s)", self.emergency_contact_name, self.emergency_contact_phone)

    def format_alert_message(
        self,
        driver_name: str,
        reason: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> str:
        """
        Constructs concise, standardized emergency SMS text.
        Adheres to medical safety guidelines: describes detected warning signs
        without claiming a confirmed medical diagnosis.
        Handles missing GPS with an explicit message.
        """
        msg = f"SAFETY ALERT: Driver {driver_name} - Fatigue / sustained drowsiness warning signs detected.\n"
        msg += f"Observed Indicators: {reason}\n"

        if latitude is not None and longitude is not None:
            maps_link = f"https://maps.google.com/?q={latitude:.5f},{longitude:.5f}"
            msg += f"Vehicle Location: {maps_link}"
        else:
            msg += "Vehicle Location: GPS signal unavailable"

        return msg

    def dispatch_sos(
        self,
        driver_name: str,
        reason: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> Tuple[SmsStatusEnum, str]:
        """
        Formats message and transmits via configured SMS provider with retry logic.
        Differentiates MOCK_SENT, SUBMITTED, SENT, and FAILED states.
        Records timestamped dispatch history.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        message_text = self.format_alert_message(
            driver_name=driver_name,
            reason=reason,
            latitude=latitude,
            longitude=longitude,
        )

        attempts = 0
        success = False
        last_error = None

        while attempts < self.max_retries and not success:
            attempts += 1
            try:
                success = self.sms_provider.send_sms(
                    recipient_phone=self.emergency_contact_phone,
                    message_text=message_text,
                )
                if success:
                    break
            except Exception as exc:
                last_error = str(exc)
                logger.error("SMS dispatch error (attempt %d/%d): %s", attempts, self.max_retries, exc)

        if not success:
            status = SmsStatusEnum.FAILED
            logger.warning(
                "SMS dispatch failed to %s after %d attempts using provider %s",
                self.emergency_contact_phone,
                attempts,
                self.sms_provider.provider_name,
            )
        elif self.sms_provider.provider_name == "mock":
            status = SmsStatusEnum.MOCK_SENT
        else:
            status = SmsStatusEnum.SENT

        record = {
            "timestamp": now_iso,
            "recipient_phone": self.emergency_contact_phone,
            "recipient_name": self.emergency_contact_name,
            "provider": self.sms_provider.provider_name,
            "status": status.value,
            "attempts": attempts,
            "message": message_text,
            "latitude": latitude,
            "longitude": longitude,
            "error": last_error,
        }
        self.last_submission_result = record
        self.dispatch_history.append(record)

        return status, message_text
