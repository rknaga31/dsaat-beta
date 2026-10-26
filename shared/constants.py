"""
Multimodal Driver Drowsiness and Health Monitoring System
Shared System Constants, Enums, and Thresholds

All modules (Backend, AI Vision, Device Integration, Alerts SOS) must import
and reference these definitions to ensure consistent system behavior and avoid drift.
"""

from enum import Enum


class EyeStatusEnum(str, Enum):
    """Classification of detected eye state."""
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    PARTIAL = "PARTIAL"
    UNKNOWN = "UNKNOWN"


class SensorDataSourceEnum(str, Enum):
    """Origin of physiological or biometric sensor data."""
    BOULT_BLE = "boult_ble"
    SIMULATED = "simulated"
    MANUAL_INJECT = "manual_inject"
    GOOGLE_HEALTH = "google_health_connect"
    UNKNOWN = "unknown"


class SensorDataStatusEnum(str, Enum):
    """
    Integrity and availability status of biometric sensor readings.
    Explicitly supports genuine, historical, synthetic, stale, and unavailable states.
    """
    CONNECTED_LIVE = "CONNECTED_LIVE"
    CONNECTED_HISTORICAL = "CONNECTED_HISTORICAL"
    SIMULATED_DEMO = "SIMULATED_DEMO"
    UNAVAILABLE = "UNAVAILABLE"
    STALE_DATA = "STALE_DATA"

    # Backward compatibility aliases
    LIVE = "CONNECTED_LIVE"
    SIMULATED = "SIMULATED_DEMO"
    STALE = "STALE_DATA"


class GpsFreshnessEnum(str, Enum):
    """Freshness status of GPS coordinates."""
    LIVE = "LIVE"
    STALE = "STALE"
    UNAVAILABLE = "UNAVAILABLE"
    SIMULATED = "SIMULATED"


class GpsPermissionEnum(str, Enum):
    """Permission state of smartphone / browser GPS."""
    GRANTED = "GRANTED"
    DENIED = "DENIED"
    PROMPT = "PROMPT"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_REQUESTED = "NOT_REQUESTED"


class EscalationStageEnum(str, Enum):
    """Driver warning and family emergency escalation workflow."""
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    HIGH_RISK = "HIGH_RISK"
    ESCALATION_PENDING = "ESCALATION_PENDING"
    FAMILY_SMS = "FAMILY_SMS"


class RiskStateEnum(str, Enum):
    """Fused multimodal driver risk assessment classification."""
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    HIGH_RISK = "HIGH_RISK"
    MONITORING_UNAVAILABLE = "MONITORING_UNAVAILABLE"


class AlertLevelEnum(str, Enum):
    """Escalation tier for audible, visual, and remote alerts."""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class BeepStatusEnum(str, Enum):
    """Operational status of the in-cabin acoustic warning buzzer."""
    INACTIVE = "INACTIVE"
    ACTIVE = "ACTIVE"
    MUTED = "MUTED"
    FAILED = "FAILED"


class SmsStatusEnum(str, Enum):
    """Delivery status of emergency SMS notifications."""
    NOT_TRIGGERED = "NOT_TRIGGERED"
    ESCALATION_PENDING = "ESCALATION_PENDING"
    QUEUED = "QUEUED"
    SUBMITTED = "SUBMITTED"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    MOCK_SENT = "MOCK_SENT"
    FAILED = "FAILED"


class LocationStatusEnum(str, Enum):
    """Reliability and availability of geographical coordinates."""
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    APPROXIMATE = "APPROXIMATE"
    SIMULATED = "SIMULATED"


# System Timing and Threshold Constants
DEFAULT_EYE_CLOSURE_DROWSY_THRESHOLD_MS = 1500.0  # Eye closure > 1.5s triggers warning
DEFAULT_EYE_CLOSURE_CRITICAL_THRESHOLD_MS = 2500.0  # Eye closure > 2.5s triggers high risk
DEFAULT_YAWN_DROWSY_THRESHOLD_MS = 2000.0
DEFAULT_HEAD_NOD_PITCH_THRESHOLD_DEG = 25.0

# Heart Rate Abnormal Ranges (beats per minute)
HEART_RATE_DROWSY_LOWER_BPM = 50.0  # Bradycardia or severe relaxation in drivers
HEART_RATE_DISTRESS_UPPER_BPM = 115.0  # Elevated stress/panic condition

# Alert Cooldowns (in seconds to prevent alert floods / SMS spam)
DEFAULT_SMS_COOLDOWN_SECONDS = 120
DEFAULT_BEEP_REPEAT_INTERVAL_SECONDS = 2
DEFAULT_ACK_WINDOW_SECONDS = 10.0  # Time for driver to silence alert before family SMS escalation

