"""
Mock SMS Provider.
Safe local test sender that validates numbers and records dispatches in memory
without making external network requests or incurring mobile charges.
"""

import logging
import re
from datetime import datetime, timezone
from typing import List, Dict, Any
from alerts_sos.sms_provider import BaseSMSProvider

logger = logging.getLogger("mock_sms")


class MockSMSProvider(BaseSMSProvider):
    """Logs simulated SMS dispatches and tracks message history for unit testing."""

    def __init__(self):
        self.sent_messages: List[Dict[str, Any]] = []

    @property
    def provider_name(self) -> str:
        return "mock"

    def send_sms(self, recipient_phone: str, message_text: str) -> bool:
        # Validate international E.164 phone format e.g. +919876543210
        e164_pattern = r"^\+[1-9]\d{1,14}$"
        if not re.match(e164_pattern, recipient_phone):
            logger.error(
                f"[MOCK SMS REJECTED] Recipient phone '{recipient_phone}' is not valid E.164 format."
            )
            return False

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "recipient": recipient_phone,
            "message": message_text,
            "char_count": len(message_text),
            "simulated_delivery": "SUCCESS",
        }
        self.sent_messages.append(record)
        logger.info(
            f"\n[MOCK SMS DISPATCHED] -> To: {recipient_phone}\nMessage: {message_text}\n"
        )
        return True

    def get_sent_messages(self) -> List[Dict[str, Any]]:
        """Returns chronological list of simulated SMS dispatches."""
        return list(self.sent_messages)

    def clear(self):
        """Clears sent messages list (useful in unit tests)."""
        self.sent_messages.clear()
