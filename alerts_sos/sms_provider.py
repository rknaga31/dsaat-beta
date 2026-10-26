"""
SMS Provider Abstract Interface.
Declares contract for dispatching emergency alert messages.
"""

from abc import ABC, abstractmethod


class BaseSMSProvider(ABC):
    """Abstract interface for SMS transmission backends (Mock, Twilio, Fast2SMS)."""

    @abstractmethod
    def send_sms(self, recipient_phone: str, message_text: str) -> bool:
        """
        Dispatches SMS text to recipient phone number in E.164 format (e.g. +919876543210).
        Returns True if successfully accepted/queued by provider, False otherwise.
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Returns readable name of SMS provider backend."""
        pass
