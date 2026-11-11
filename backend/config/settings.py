"""
Application Settings & Environment Configuration.
Loads system settings from environment variables or .env file with safe fallbacks.
"""

import os
from functools import lru_cache
from typing import List
from dotenv import load_dotenv

# Load local environment variables if present
load_dotenv()


class Settings:
    """System runtime configuration model."""

    APP_ENV: str = os.getenv("APP_ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Network Host & Port
    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))

    # CORS Allowed Origins
    ALLOWED_ORIGINS: List[str] = [
        origin.strip()
        for origin in os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000",
        ).split(",")
        if origin.strip()
    ]

    # Sensor & Hardware Configuration
    SMARTWATCH_SOURCE: str = os.getenv("SMARTWATCH_SOURCE", "SIMULATED")
    BOULT_MAC_ADDRESS: str = os.getenv("BOULT_MAC_ADDRESS", "00:00:00:00:00:00")
    GPS_SOURCE: str = os.getenv("GPS_SOURCE", "MOCK")

    # Alerts & Notifications
    SMS_PROVIDER: str = os.getenv("SMS_PROVIDER", "mock")
    ENABLE_AUDIO_BEEPS: bool = os.getenv("ENABLE_AUDIO_BEEPS", "true").lower() in ("true", "1", "yes")
    ALERT_SMS_COOLDOWN_SECONDS: int = int(os.getenv("ALERT_SMS_COOLDOWN_SECONDS", "120"))
    ALERT_DEBOUNCE_WINDOW_MS: int = int(os.getenv("ALERT_DEBOUNCE_WINDOW_MS", "500"))
    ALERT_ACK_WINDOW_SECONDS: float = float(os.getenv("ALERT_ACK_WINDOW_SECONDS", "10.0"))

    # Free Email Alert Configuration (Zero-cost via Gmail / Outlook SMTP)
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    EMERGENCY_CONTACT_EMAIL: str = os.getenv("EMERGENCY_CONTACT_EMAIL", "")

    # Free Telegram Bot Configuration (Zero-cost via Telegram API)
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

    # Emergency Contact
    EMERGENCY_CONTACT_PHONE: str = os.getenv("EMERGENCY_CONTACT_PHONE", "+910000000000")
    EMERGENCY_CONTACT_NAME: str = os.getenv("EMERGENCY_CONTACT_NAME", "Primary Emergency Contact")


@lru_cache()
def get_settings() -> Settings:
    """Returns singleton cached settings instance."""
    return Settings()
