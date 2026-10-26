"""
Backend Data Models & Persistence Layer.
Provides database schemas and entity representations for historical trip data.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List


@dataclass
class DriverProfileModel:
    """Represents registered driver profile."""
    driver_id: str
    full_name: str
    emergency_contact_phone: str
    emergency_contact_name: str
    baseline_resting_bpm: float = 72.0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class TripSessionModel:
    """Represents a completed or in-progress trip."""
    session_id: str
    driver_id: str
    start_time: str
    end_time: Optional[str] = None
    max_risk_score: float = 0.0
    total_warnings: int = 0
    total_critical_alerts: int = 0
    notes: Optional[str] = None
