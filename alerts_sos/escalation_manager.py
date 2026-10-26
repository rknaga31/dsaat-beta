"""
Escalation Manager.
Orchestrates alert escalation tiers, driver acknowledgement grace windows,
anti-spam cooldowns, duplicate-alert prevention, and coordinates the BeepManager
and FamilyNotificationService.

Escalation Workflow:
NORMAL -> WARNING -> HIGH_RISK -> ESCALATION_PENDING -> FAMILY_SMS
"""

import time
import uuid
from datetime import datetime, timezone
from typing import Optional, Set, Dict, Any
from backend.schemas.risk_schema import RiskStateSchema
from backend.schemas.alert_schema import AlertEventSchema
from shared.constants import (
    RiskStateEnum,
    AlertLevelEnum,
    BeepStatusEnum,
    SmsStatusEnum,
    LocationStatusEnum,
    EscalationStageEnum,
    DEFAULT_ACK_WINDOW_SECONDS,
)
from alerts_sos.beep_manager import BeepManager
from alerts_sos.family_notification import FamilyNotificationService


class EscalationManager:
    """Consumes risk evaluations and enforces debounce/cooldown rules before firing alerts."""

    def __init__(
        self,
        beep_manager: BeepManager,
        family_service: FamilyNotificationService,
        sms_cooldown_seconds: int = 120,
        ack_window_seconds: float = 0.0,
    ):
        self.beep_manager = beep_manager
        self.family_service = family_service
        self.sms_cooldown_seconds = sms_cooldown_seconds
        self.ack_window_seconds = ack_window_seconds

        self._last_sms_sent_time: float = 0.0
        self._current_level = AlertLevelEnum.INFO
        self._escalation_stage = EscalationStageEnum.NORMAL

        # State tracking for unresolved events and acknowledgement window
        self._active_event_id: Optional[str] = None
        self._high_risk_started_at: Optional[float] = None
        self._dispatched_sms_events: Set[str] = set()
        self._acknowledged_events: Set[str] = set()
        self._last_alert_event: Optional[AlertEventSchema] = None

    @property
    def escalation_stage(self) -> EscalationStageEnum:
        return self._escalation_stage

    @property
    def is_escalation_pending(self) -> bool:
        return self._escalation_stage == EscalationStageEnum.ESCALATION_PENDING

    @property
    def remaining_ack_seconds(self) -> float:
        """Returns seconds remaining before pending escalation triggers family SMS."""
        if not self._high_risk_started_at or self.ack_window_seconds <= 0:
            return 0.0
        elapsed = time.time() - self._high_risk_started_at
        return max(0.0, round(self.ack_window_seconds - elapsed, 1))

    def acknowledge_alert(self) -> Dict[str, Any]:
        """
        Driver acknowledgement action.
        Silences the cabin buzzer and cancels pending family SMS escalation.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        self.beep_manager.stop_warning()

        canceled_sms = False
        if self._active_event_id:
            self._acknowledged_events.add(self._active_event_id)
            if self._escalation_stage == EscalationStageEnum.ESCALATION_PENDING:
                canceled_sms = True

        self._escalation_stage = EscalationStageEnum.NORMAL
        self._high_risk_started_at = None

        if self._last_alert_event:
            self._last_alert_event.driver_beep_status = BeepStatusEnum.MUTED
            if canceled_sms:
                self._last_alert_event.family_sms_status = SmsStatusEnum.NOT_TRIGGERED

        return {
            "timestamp": now_iso,
            "status": "ACKNOWLEDGED",
            "action": "buzzer_silenced_and_sms_canceled" if canceled_sms else "buzzer_silenced",
            "event_id": self._active_event_id,
        }

    def process_risk_update(
        self,
        risk_state: RiskStateSchema,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> Optional[AlertEventSchema]:
        """
        Evaluates risk state and transitions through escalation stages:
        WARNING -> HIGH_RISK -> ESCALATION_PENDING -> FAMILY_SMS
        """
        now = time.time()
        now_iso = datetime.now(timezone.utc).isoformat()

        # Graceful recovery when state returns to NORMAL
        if risk_state.state == RiskStateEnum.NORMAL:
            self.beep_manager.stop_warning()
            self._current_level = AlertLevelEnum.INFO
            self._escalation_stage = EscalationStageEnum.NORMAL
            self._active_event_id = None
            self._high_risk_started_at = None
            self._last_alert_event = None
            return None

        # Warning when monitoring becomes unavailable
        if risk_state.state == RiskStateEnum.MONITORING_UNAVAILABLE:
            self.beep_manager.play_monitoring_unavailable()
            self._escalation_stage = EscalationStageEnum.NORMAL
            return None

        # Build primary reason string
        reason = (
            "; ".join(risk_state.contributing_reasons)
            if risk_state.contributing_reasons
            else f"Risk state evaluated as {risk_state.state.value}"
        )

        location_status = (
            LocationStatusEnum.AVAILABLE
            if latitude is not None and longitude is not None
            else LocationStatusEnum.UNAVAILABLE
        )

        # Stage 1: WARNING -> Audible cabin beep, NO family SMS
        if risk_state.state == RiskStateEnum.WARNING:
            beep_status = self.beep_manager.play_warning(AlertLevelEnum.WARNING)
            self._current_level = AlertLevelEnum.WARNING
            self._escalation_stage = EscalationStageEnum.WARNING
            self._active_event_id = None
            self._high_risk_started_at = None

            event = AlertEventSchema(
                event_id=str(uuid.uuid4()),
                timestamp=now_iso,
                alert_level=AlertLevelEnum.WARNING,
                reason=reason,
                driver_beep_status=beep_status,
                family_sms_status=SmsStatusEnum.NOT_TRIGGERED,
                location_status=location_status,
                latitude=latitude,
                longitude=longitude,
            )
            self._last_alert_event = event
            return event

        # Stage 2 & 3: HIGH_RISK -> ESCALATION_PENDING -> FAMILY_SMS
        if risk_state.state == RiskStateEnum.HIGH_RISK:
            beep_status = self.beep_manager.play_warning(AlertLevelEnum.CRITICAL)
            self._current_level = AlertLevelEnum.CRITICAL

            # Initialize unresolved incident identifier and timer
            if not self._active_event_id:
                self._active_event_id = str(uuid.uuid4())
                self._high_risk_started_at = now

            event_id = self._active_event_id

            # Check if this incident was already acknowledged by the driver
            if event_id in self._acknowledged_events:
                return AlertEventSchema(
                    event_id=event_id,
                    timestamp=now_iso,
                    alert_level=AlertLevelEnum.CRITICAL,
                    reason=reason,
                    driver_beep_status=BeepStatusEnum.MUTED,
                    family_sms_status=SmsStatusEnum.NOT_TRIGGERED,
                    location_status=location_status,
                    latitude=latitude,
                    longitude=longitude,
                )

            elapsed_high_risk = now - (self._high_risk_started_at or now)

            # Check driver acknowledgement grace window
            if self.ack_window_seconds > 0 and elapsed_high_risk < self.ack_window_seconds:
                self._escalation_stage = EscalationStageEnum.ESCALATION_PENDING
                event = AlertEventSchema(
                    event_id=event_id,
                    timestamp=now_iso,
                    alert_level=AlertLevelEnum.CRITICAL,
                    reason=f"[ESCALATION PENDING: {round(self.ack_window_seconds - elapsed_high_risk, 1)}s] {reason}",
                    driver_beep_status=beep_status,
                    family_sms_status=SmsStatusEnum.ESCALATION_PENDING,
                    location_status=location_status,
                    latitude=latitude,
                    longitude=longitude,
                )
                self._last_alert_event = event
                return event

            # Acknowledgement window expired: Escalate to FAMILY_SMS
            self._escalation_stage = EscalationStageEnum.FAMILY_SMS

            # Check deduplication for this active incident and global cooldown
            time_since_last_sms = now - self._last_sms_sent_time
            if event_id not in self._dispatched_sms_events and time_since_last_sms >= self.sms_cooldown_seconds:
                sms_status, _ = self.family_service.dispatch_sos(
                    driver_name="Primary Driver",
                    reason=reason,
                    latitude=latitude,
                    longitude=longitude,
                )
                self._last_sms_sent_time = now
                self._dispatched_sms_events.add(event_id)
            else:
                # Deduplication / Cooldown active: prevent spamming family for same incident
                sms_status = SmsStatusEnum.NOT_TRIGGERED

            event = AlertEventSchema(
                event_id=event_id,
                timestamp=now_iso,
                alert_level=AlertLevelEnum.CRITICAL,
                reason=reason,
                driver_beep_status=beep_status,
                family_sms_status=sms_status,
                location_status=location_status,
                latitude=latitude,
                longitude=longitude,
            )
            self._last_alert_event = event
            return event

        return None
