"""
Real SMS Providers for Live Emergency Cellular Alerts.
Supports:
1. Twilio (Global standard, REST API)
2. Fast2SMS (Indian carrier SMS gateway)
3. Fallback to MockSMSProvider with clear warnings if credentials are missing.
"""

import os
import re
import logging
from typing import Optional
import requests
from alerts_sos.sms_provider import BaseSMSProvider

logger = logging.getLogger("real_sms_provider")


class TwilioSMSProvider(BaseSMSProvider):
    """Dispatches real SMS using Twilio REST API."""

    def __init__(
        self,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        from_number: Optional[str] = None,
    ):
        self.account_sid = account_sid or os.getenv("TWILIO_ACCOUNT_SID", "")
        self.auth_token = auth_token or os.getenv("TWILIO_AUTH_TOKEN", "")
        self.from_number = from_number or os.getenv("TWILIO_PHONE_NUMBER", "")

    @property
    def provider_name(self) -> str:
        return "twilio"

    @property
    def is_configured(self) -> bool:
        return bool(self.account_sid and self.auth_token and self.from_number)

    def send_sms(self, recipient_phone: str, message_text: str) -> bool:
        if not self.is_configured:
            logger.warning(
                "[TWILIO SMS NOT CONFIGURED] Missing TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, or TWILIO_PHONE_NUMBER in .env."
            )
            return False

        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
        data = {
            "To": recipient_phone,
            "From": self.from_number,
            "Body": message_text,
        }

        try:
            response = requests.post(
                url,
                data=data,
                auth=(self.account_sid, self.auth_token),
                timeout=5.0,
            )
            if response.status_code in (200, 201):
                logger.info(f"[REAL TWILIO SMS SENT] Successfully dispatched to {recipient_phone}")
                return True
            else:
                logger.error(
                    f"[TWILIO ERROR {response.status_code}] Failed to send SMS: {response.text}"
                )
                return False
        except Exception as exc:
            logger.error(f"[TWILIO NETWORK FAULT] {exc}")
            return False


class Fast2SMSProvider(BaseSMSProvider):
    """Dispatches real SMS in India using Fast2SMS Gateway."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("FAST2SMS_API_KEY", "")

    @property
    def provider_name(self) -> str:
        return "fast2sms"

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def send_sms(self, recipient_phone: str, message_text: str) -> bool:
        if not self.is_configured:
            logger.warning("[FAST2SMS NOT CONFIGURED] Missing FAST2SMS_API_KEY in .env.")
            return False

        # Extract 10-digit number for Indian gateway
        clean_number = re.sub(r"[^\d]", "", recipient_phone)[-10:]
        url = "https://www.fast2sms.com/dev/bulkV2"
        headers = {
            "authorization": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "route": "q",
            "message": message_text,
            "language": "english",
            "flash": 0,
            "numbers": clean_number,
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=5.0)
            res_data = response.json()
            if res_data.get("return") is True or response.status_code == 200:
                logger.info(f"[FAST2SMS SENT] Dispatched to {clean_number}")
                return True
            else:
                logger.error(f"[FAST2SMS ERROR] {res_data}")
                return False
        except Exception as exc:
            logger.error(f"[FAST2SMS FAULT] {exc}")
            return False
