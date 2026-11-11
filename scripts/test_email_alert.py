"""
Test Script: Send a Live Test Emergency Email with GPS Pin.
Run this script to verify that your Gmail / SMTP configuration is working properly.
Usage:
    python scripts/test_email_alert.py
"""

import sys
import os
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from alerts_sos.free_providers import EmailNotificationProvider
from alerts_sos.family_notification import FamilyNotificationService


def run_test():
    print("\n=======================================================")
    print("  D-SAAT: Emergency Email Notification Test")
    print("=======================================================\n")

    provider = EmailNotificationProvider()
    print(f"Provider Name   : {provider.provider_name}")
    print(f"SMTP Host       : {provider.smtp_host}:{provider.smtp_port}")
    print(f"Sender Email    : {provider.smtp_user or '[NOT SET in .env]'}")
    print(f"Recipient Email : {provider.default_recipient or '[NOT SET in .env]'}")
    print(f"Configured?     : {'YES (Ready)' if provider.is_configured else 'NO (Missing SMTP_USER or SMTP_PASSWORD in .env)'}\n")

    if not provider.is_configured:
        print("[!] To send a real test email, open .env and set:")
        print("    SMS_PROVIDER=email")
        print("    SMTP_USER=your_email@gmail.com")
        print("    SMTP_PASSWORD=your_16_char_google_app_password")
        print("    EMERGENCY_CONTACT_EMAIL=family_recipient@gmail.com\n")
        print("    (Get your free App Password at: https://myaccount.google.com/apppasswords)")
        return

    family_service = FamilyNotificationService(
        sms_provider=provider,
        emergency_contact_phone=provider.default_recipient,
        emergency_contact_name="Family Emergency Contact",
    )

    print(f"Sending test emergency alert to: {provider.default_recipient} ...")
    status, details = family_service.dispatch_sos(
        driver_name="Test Driver",
        reason="Test Simulation - Sustained Eye Closure (Micro-sleep)",
        latitude=12.9716,
        longitude=77.5946,
    )

    print(f"\nResult Status : {status.value}")
    print(f"Details       : {details}\n")
    if "SENT" in status.value:
        print("[SUCCESS] Check the recipient inbox (and Spam folder just in case)!")


if __name__ == "__main__":
    run_test()
