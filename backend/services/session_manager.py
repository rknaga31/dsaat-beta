"""
Session Manager Service.
Tracks driver trip sessions, duration, driving fatigue accumulation,
maintains the latest telemetry state for the real-time dashboard,
and orchestrates the alerts escalation manager.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from backend.schemas.vision_schema import VisionEventSchema
from backend.schemas.sensor_schema import SensorReadingSchema
from backend.schemas.risk_schema import RiskStateSchema
from backend.schemas.alert_schema import AlertEventSchema
from device_integration.android_gps.location_schema import GPSLocationSchema
from backend.services.risk_engine import risk_engine
from backend.services.event_logger import event_logger
from alerts_sos import default_escalation_manager, EscalationManager
from shared.constants import RiskStateEnum, BeepStatusEnum, GpsFreshnessEnum, GpsPermissionEnum


class SessionManager:
    """Coordinates driver session lifecycle and holds current telemetry state."""

    def __init__(self, escalation_manager: Optional[EscalationManager] = None):
        self.session_id: Optional[str] = None
        self.driver_id: Optional[str] = None
        self.start_time: Optional[datetime] = None
        self.is_active: bool = False

        # Current cached telemetry
        self.latest_vision_event: Optional[VisionEventSchema] = None
        self.latest_sensor_reading: Optional[SensorReadingSchema] = None
        self.latest_risk_state: Optional[RiskStateSchema] = None
        self.latest_alert: Optional[AlertEventSchema] = None

        # Vehicle position telemetry
        self.latest_latitude: Optional[float] = None
        self.latest_longitude: Optional[float] = None
        self.latest_gps_location: Optional[GPSLocationSchema] = None

        # Integrated alerts and escalation manager
        self.escalation_manager = escalation_manager or default_escalation_manager

    def start_session(self, driver_id: str = "driver_default") -> Dict[str, Any]:
        """Initiates a new driving monitoring session."""
        self.session_id = str(uuid.uuid4())
        self.driver_id = driver_id
        self.start_time = datetime.now(timezone.utc)
        self.is_active = True

        session_info = {
            "session_id": self.session_id,
            "driver_id": self.driver_id,
            "start_time": self.start_time.isoformat(),
            "status": "ACTIVE",
        }
        event_logger.log_event("session_started", session_info)
        return session_info

    def end_session(self) -> Dict[str, Any]:
        """Terminates the current driving monitoring session and silences active alerts."""
        if not self.is_active or not self.start_time:
            return {"status": "NO_ACTIVE_SESSION"}

        end_time = datetime.now(timezone.utc)
        duration_seconds = (end_time - self.start_time).total_seconds()
        summary = {
            "session_id": self.session_id,
            "driver_id": self.driver_id,
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": round(duration_seconds, 1),
            "status": "COMPLETED",
        }
        self.is_active = False
        self.escalation_manager.beep_manager.stop_warning()
        self.latest_alert = None
        event_logger.log_event("session_ended", summary)
        return summary

    def update_vision(self, vision_event: VisionEventSchema) -> RiskStateSchema:
        """Receives new vision telemetry and triggers fresh risk calculation and alert escalation."""
        self.latest_vision_event = vision_event
        return self._recalculate_risk()

    def update_sensor(self, sensor_reading: SensorReadingSchema) -> RiskStateSchema:
        """Receives new biometric telemetry and triggers fresh risk calculation and alert escalation."""
        self.latest_sensor_reading = sensor_reading
        return self._recalculate_risk()

    def update_gps_location(self, location: GPSLocationSchema) -> Dict[str, Any]:
        """Updates comprehensive GPS telemetry from phone bridge or browser Geolocation."""
        self.latest_gps_location = location
        self.latest_latitude = location.latitude
        self.latest_longitude = location.longitude

        gps_record = location.model_dump()
        event_logger.log_event("gps_position_updated", gps_record)
        return gps_record

    def update_gps(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Updates live geographical position from GPS bridge (backward compatible)."""
        now_iso = datetime.now(timezone.utc).isoformat()
        loc = GPSLocationSchema(
            timestamp=now_iso,
            latitude=latitude,
            longitude=longitude,
            source="android_gps_bridge",
            permission_status=GpsPermissionEnum.GRANTED,
            freshness_status=GpsFreshnessEnum.LIVE,
            is_valid=True,
        )
        return self.update_gps_location(loc)

    def acknowledge_alert(self) -> Dict[str, Any]:
        """Silences cabin buzzer and updates active alert status."""
        ack_record = self.escalation_manager.acknowledge_alert()
        if self.latest_alert:
            self.latest_alert.driver_beep_status = BeepStatusEnum.MUTED
        event_logger.log_event("alert_acknowledged", ack_record)
        return ack_record

    def _recalculate_risk(self) -> RiskStateSchema:
        """Re-evaluates multimodal risk state and coordinates alert escalation."""
        new_risk = risk_engine.evaluate_risk(
            vision_event=self.latest_vision_event,
            sensor_reading=self.latest_sensor_reading,
        )

        # Log transition if risk escalated
        if (
            self.latest_risk_state
            and new_risk.state != self.latest_risk_state.state
            and new_risk.state in (RiskStateEnum.WARNING, RiskStateEnum.HIGH_RISK)
        ):
            event_logger.log_event(
                "risk_escalation",
                {
                    "from_state": self.latest_risk_state.state,
                    "to_state": new_risk.state,
                    "score": new_risk.risk_score,
                    "reasons": new_risk.contributing_reasons,
                },
            )

        self.latest_risk_state = new_risk

        # Trigger integrated alert escalation
        alert_event = self.escalation_manager.process_risk_update(
            risk_state=new_risk,
            latitude=self.latest_latitude,
            longitude=self.latest_longitude,
        )
        if alert_event:
            self.latest_alert = alert_event
            event_logger.log_event("alert_dispatched", alert_event.model_dump())
        elif new_risk.state == RiskStateEnum.NORMAL:
            self.latest_alert = None

        return new_risk

    def get_current_status(self) -> Dict[str, Any]:
        """Provides combined status packet for frontend dashboard delivery."""
        duration_s = 0.0
        if self.is_active and self.start_time:
            duration_s = (datetime.now(timezone.utc) - self.start_time).total_seconds()

        # Build GPS packet
        if self.latest_gps_location:
            gps_packet = self.latest_gps_location.model_dump()
        elif self.latest_latitude is not None and self.latest_longitude is not None:
            gps_packet = {
                "latitude": self.latest_latitude,
                "longitude": self.latest_longitude,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "android_gps_bridge",
                "permission_status": "GRANTED",
                "freshness_status": "LIVE",
                "is_valid": True,
            }
        else:
            gps_packet = {
                "latitude": None,
                "longitude": None,
                "timestamp": None,
                "source": "none",
                "permission_status": "NOT_REQUESTED",
                "freshness_status": "UNAVAILABLE",
                "is_valid": False,
                "error_state": "Awaiting mobile phone GPS connection.",
            }

        return {
            "session_id": self.session_id,
            "is_active": self.is_active,
            "trip_duration_seconds": round(duration_s, 1),
            "risk_state": (
                self.latest_risk_state.model_dump()
                if self.latest_risk_state
                else None
            ),
            "active_alert": (
                self.latest_alert.model_dump()
                if self.latest_alert
                else None
            ),
            "buzzer_status": self.escalation_manager.beep_manager.status.value,
            "vision": (
                self.latest_vision_event.model_dump()
                if self.latest_vision_event
                else None
            ),
            "sensor": (
                self.latest_sensor_reading.model_dump()
                if self.latest_sensor_reading
                else None
            ),
            "gps": gps_packet,
            "escalation": {
                "stage": self.escalation_manager.escalation_stage.value,
                "is_pending": self.escalation_manager.is_escalation_pending,
                "remaining_ack_seconds": self.escalation_manager.remaining_ack_seconds,
                "last_sms_result": self.escalation_manager.family_service.last_submission_result,
                "sms_provider": self.escalation_manager.family_service.sms_provider.provider_name,
                "emergency_contact_phone": self.escalation_manager.family_service.emergency_contact_phone,
                "emergency_contact_name": self.escalation_manager.family_service.emergency_contact_name,
            },
        }


# Global singleton instance
session_manager = SessionManager()
