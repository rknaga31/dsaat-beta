"""
Free Zero-Cost Emergency Alert Providers.
Dispatches critical driver safety notifications with live Google Maps GPS coordinates
via 100% free channels:
1. Email Notification Provider (via standard Gmail / Outlook SMTP using Python smtplib)
2. Telegram Bot Notification Provider (via free Telegram Bot API)
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import requests

from alerts_sos.sms_provider import BaseSMSProvider

logger = logging.getLogger("free_alert_providers")


class EmailNotificationProvider(BaseSMSProvider):
    """
    Dispatches 100% free emergency email alerts using Python's built-in smtplib.
    Works with Gmail (using free App Password), Outlook, Yahoo, or any standard SMTP server.
    Zero external subscription fees, zero API charges.
    """

    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        default_recipient: Optional[str] = None,
    ):
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(smtp_port or os.getenv("SMTP_PORT", "587"))
        self.smtp_user = smtp_user or os.getenv("SMTP_USER", "")
        self.smtp_password = smtp_password or os.getenv("SMTP_PASSWORD", "")
        self.default_recipient = default_recipient or os.getenv("EMERGENCY_CONTACT_EMAIL", "")

    @property
    def provider_name(self) -> str:
        return "free_email_smtp"

    @property
    def is_configured(self) -> bool:
        return bool(self.smtp_user and self.smtp_password)

    def send_sms(self, recipient_phone: str, message_text: str) -> bool:
        """
        Sends the emergency alert as an email.
        If recipient_phone contains an '@', it uses it directly; otherwise falls back
        to EMERGENCY_CONTACT_EMAIL or default_recipient.
        """
        target_email = recipient_phone if "@" in recipient_phone else self.default_recipient

        if not self.is_configured:
            logger.warning(
                "[EMAIL NOT CONFIGURED] Set SMTP_USER and SMTP_PASSWORD in .env to enable free email alerts. "
                f"Alert would have been sent to: {target_email or 'None'}"
            )
            return False

        if not target_email or "@" not in target_email:
            logger.error("[EMAIL ERROR] No valid recipient email address configured.")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "🚨 URGENT: Driver Safety & Fatigue Alert (Live GPS Pin)"
            msg["From"] = f"D-SAAT Safety System <{self.smtp_user}>"
            msg["To"] = target_email

            # Create clean HTML and Plain Text bodies
            plain_text = message_text
            html_text = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 2px solid #ef4444; border-radius: 10px; background-color: #0f172a; color: #f8fafc;">
                <div style="text-align: center; margin-bottom: 20px;">
                    <h2 style="color: #ef4444; margin: 0;">🚨 D-SAAT DRIVER SAFETY ALERT</h2>
                    <p style="color: #94a3b8; font-size: 0.9em; margin-top: 5px;">Autonomous Emergency Telemetry System</p>
                </div>
                <div style="background-color: #1e293b; padding: 15px; border-radius: 8px; margin-bottom: 20px; line-height: 1.6; border-left: 4px solid #ef4444;">
                    <pre style="white-space: pre-wrap; font-family: monospace; font-size: 14px; color: #e2e8f0; margin: 0;">{message_text}</pre>
                </div>
                <p style="color: #64748b; font-size: 0.8em; text-align: center; margin-top: 25px;">
                    This is an automated safety alert dispatched by D-SAAT Beta. Please check on the driver immediately.
                </p>
            </div>
            """

            msg.attach(MIMEText(plain_text, "plain"))
            msg.attach(MIMEText(html_text, "html"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10.0) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"[FREE EMAIL SENT] Emergency alert successfully emailed to {target_email}")
            return True

        except Exception as exc:
            logger.error(f"[EMAIL SEND FAILED] Error transmitting alert via SMTP: {exc}")
            return False


class TelegramNotificationProvider(BaseSMSProvider):
    """
    Dispatches 100% free emergency instant messages via the Telegram Bot API.
    Zero subscription cost, delivers instant push notifications with sound on iOS and Android.
    """

    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
    ):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID", "")

    @property
    def provider_name(self) -> str:
        return "free_telegram_bot"

    @property
    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    def send_sms(self, recipient_phone: str, message_text: str) -> bool:
        """Sends emergency alert via Telegram Bot API."""
        target_chat = self.chat_id if not recipient_phone.startswith("@") else recipient_phone

        if not self.is_configured:
            logger.warning(
                "[TELEGRAM NOT CONFIGURED] Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env. "
                "Telegram alerts are completely free of cost."
            )
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": target_chat,
            "text": f"🚨 *D-SAAT EMERGENCY ALERT*\n\n{message_text}",
            "parse_mode": "Markdown",
            "disable_web_page_preview": False,
        }

        try:
            resp = requests.post(url, json=payload, timeout=5.0)
            if resp.status_code == 200:
                logger.info(f"[TELEGRAM ALERT SENT] Successfully dispatched to chat {target_chat}")
                return True
            else:
                logger.error(f"[TELEGRAM API ERROR {resp.status_code}] {resp.text}")
                return False
        except Exception as exc:
            logger.error(f"[TELEGRAM NETWORK ERROR] {exc}")
            return False
