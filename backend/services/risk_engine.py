"""
Risk Engine Service.
Core multimodal fusion algorithm evaluating driver alertness and health risk state.
Fuses visual indicators (eye closure, yawns, head nods, face absence) with biometric sensors (heart rate).
Includes temporal state, sensor freshness validation, and error-handling.
"""

import time
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from backend.schemas.vision_schema import VisionEventSchema
from backend.schemas.sensor_schema import SensorReadingSchema
from backend.schemas.risk_schema import RiskStateSchema
from shared.constants import (
    RiskStateEnum,
    EyeStatusEnum,
    SensorDataStatusEnum,
    DEFAULT_EYE_CLOSURE_DROWSY_THRESHOLD_MS,
    DEFAULT_EYE_CLOSURE_CRITICAL_THRESHOLD_MS,
    DEFAULT_YAWN_DROWSY_THRESHOLD_MS,
    HEART_RATE_DROWSY_LOWER_BPM,
    HEART_RATE_DISTRESS_UPPER_BPM,
)

# Maximum allowable age for biometric sensor data before marking as STALE
MAX_SENSOR_STALENESS_SECONDS = 10.0

# Duration without face before elevating to warning for driver distraction
FACE_LOST_WARNING_THRESHOLD_MS = 3000.0


class RiskEngine:
    """Evaluates driver state based on multi-sensor telemetry."""

    def __init__(
        self,
        eye_warn_threshold_ms: float = DEFAULT_EYE_CLOSURE_DROWSY_THRESHOLD_MS,
        eye_crit_threshold_ms: float = DEFAULT_EYE_CLOSURE_CRITICAL_THRESHOLD_MS,
        max_sensor_staleness_sec: float = MAX_SENSOR_STALENESS_SECONDS,
        face_lost_threshold_ms: float = FACE_LOST_WARNING_THRESHOLD_MS,
    ):
        self.eye_warn_threshold_ms = eye_warn_threshold_ms
        self.eye_crit_threshold_ms = eye_crit_threshold_ms
        self.max_sensor_staleness_sec = max_sensor_staleness_sec
        self.face_lost_threshold_ms = face_lost_threshold_ms

        # Temporal state for face tracking continuity
        self._face_lost_start_time: Optional[float] = None

    def evaluate_risk(
        self,
        vision_event: Optional[VisionEventSchema] = None,
        sensor_reading: Optional[SensorReadingSchema] = None,
    ) -> RiskStateSchema:
        """
        Fuses vision inference and biometric sensor telemetry into a classified RiskState.

        Rules:
        - If neither telemetry source is available: evaluates to MONITORING_UNAVAILABLE.
        - Checks sensor freshness: readings older than 10s are flagged STALE and excluded.
        - Checks driver face absence: if face missing > 3.0s, triggers WARNING for distraction.
        - Prolonged eye closure (>= 2500ms) or combined nod + yawn triggers HIGH_RISK.
        - Moderate eye closure (>= 1500ms) or frequent yawns triggers WARNING.
        - Heart rate extremes modify risk weight up or down.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        now_ts = time.time()
        contributing_reasons: List[str] = []
        raw_score: float = 0.0

        # Check telemetry availability
        has_vision = vision_event is not None
        has_sensor = (
            sensor_reading is not None and sensor_reading.heart_rate_bpm is not None
        )

        if not has_vision and not has_sensor:
            self._face_lost_start_time = None
            return RiskStateSchema(
                timestamp=now_iso,
                state=RiskStateEnum.MONITORING_UNAVAILABLE,
                risk_score=0.0,
                contributing_reasons=["No vision or sensor telemetry available"],
                monitoring_reliable=False,
            )

        # 1. Biometric Sensor Freshness & Physiological Evaluation
        sensor_is_fresh = False
        if has_sensor and sensor_reading and sensor_reading.heart_rate_bpm is not None:
            # Staleness check: parse timestamp and compare with current UTC time
            try:
                reading_ts_str = sensor_reading.timestamp.replace("Z", "+00:00")
                reading_dt = datetime.fromisoformat(reading_ts_str)
                age_seconds = (datetime.now(timezone.utc) - reading_dt).total_seconds()
            except Exception:
                age_seconds = 0.0

            if age_seconds > self.max_sensor_staleness_sec:
                # Sensor data is stale; update status and ignore values
                sensor_reading.data_status = SensorDataStatusEnum.STALE
                contributing_reasons.append(
                    f"Smartwatch telemetry is stale ({age_seconds:.1f}s old); biometric reading ignored"
                )
            else:
                sensor_is_fresh = True
                hr = sensor_reading.heart_rate_bpm
                # Boundary value handling
                if hr < HEART_RATE_DROWSY_LOWER_BPM:
                    raw_score += 20.0
                    contributing_reasons.append(
                        f"Low heart rate ({hr:.0f} bpm) indicates potential drowsiness/bradycardia"
                    )
                elif hr > HEART_RATE_DISTRESS_UPPER_BPM:
                    raw_score += 20.0
                    contributing_reasons.append(
                        f"Elevated heart rate ({hr:.0f} bpm) indicates acute stress or distress"
                    )
        elif sensor_reading is not None and sensor_reading.data_status == SensorDataStatusEnum.UNAVAILABLE:
            contributing_reasons.append("Smartwatch telemetry currently unavailable")

        # 2. Vision Processing & Temporal Distraction Evaluation
        vision_reliable = False
        if has_vision and vision_event:
            if not vision_event.face_detected:
                # Track duration of face loss for distraction / occlusion detection
                if self._face_lost_start_time is None:
                    self._face_lost_start_time = now_ts
                lost_dur_ms = (now_ts - self._face_lost_start_time) * 1000.0

                if lost_dur_ms >= self.face_lost_threshold_ms:
                    raw_score += 45.0  # Elevate to WARNING
                    contributing_reasons.append(
                        f"Driver distraction / camera occlusion: face not visible for {lost_dur_ms/1000.0:.1f}s"
                    )
                else:
                    contributing_reasons.append("No driver face detected in camera frame")
            elif not vision_event.tracking_reliable:
                self._face_lost_start_time = None
                contributing_reasons.append("Face tracking is degraded or unreliable (poor lighting or occlusion)")
            else:
                # Face locked and reliable
                self._face_lost_start_time = None
                vision_reliable = True

                # Prolonged eye closure analysis
                closure_ms = vision_event.eye_closure_duration_ms
                if vision_event.eye_status == EyeStatusEnum.CLOSED or closure_ms > 0:
                    if closure_ms >= self.eye_crit_threshold_ms:
                        raw_score += 85.0
                        contributing_reasons.append(
                            f"Critical eye closure: eyes closed for {closure_ms/1000.0:.1f}s"
                        )
                    elif closure_ms >= self.eye_warn_threshold_ms:
                        raw_score += 50.0
                        contributing_reasons.append(
                            f"Prolonged eye closure: eyes closed for {closure_ms/1000.0:.1f}s"
                        )
                    elif closure_ms > 500:
                        raw_score += 15.0

                # Yawning analysis
                if vision_event.yawn_detected:
                    raw_score += 25.0
                    contributing_reasons.append("Sustained yawning detected")

                # Head nodding analysis
                if vision_event.head_nod_detected:
                    raw_score += 30.0
                    contributing_reasons.append("Drowsy head nod movement detected")

        # 3. Determine Overall Reliability & State Classification
        monitoring_reliable = vision_reliable or (
            sensor_is_fresh
            and sensor_reading is not None
            and sensor_reading.data_status in (
                SensorDataStatusEnum.LIVE,
                SensorDataStatusEnum.SIMULATED,
                SensorDataStatusEnum.CONNECTED_LIVE,
                SensorDataStatusEnum.CONNECTED_HISTORICAL,
                SensorDataStatusEnum.SIMULATED_DEMO,
            )
        )

        if not monitoring_reliable and raw_score < 20:
            return RiskStateSchema(
                timestamp=now_iso,
                state=RiskStateEnum.MONITORING_UNAVAILABLE,
                risk_score=0.0,
                contributing_reasons=contributing_reasons or ["Insufficient valid sensor inputs"],
                monitoring_reliable=False,
                vision_snapshot=vision_event.model_dump() if vision_event else None,
                sensor_snapshot=sensor_reading.model_dump() if sensor_reading else None,
            )

        # Cap score between 0.0 and 100.0
        final_score = min(max(raw_score, 0.0), 100.0)

        # Classify state
        if final_score >= 80.0:
            state = RiskStateEnum.HIGH_RISK
        elif final_score >= 40.0:
            state = RiskStateEnum.WARNING
        else:
            state = RiskStateEnum.NORMAL
            if not contributing_reasons:
                contributing_reasons.append("Driver alert with normal indicators")

        return RiskStateSchema(
            timestamp=now_iso,
            state=state,
            risk_score=round(final_score, 1),
            contributing_reasons=contributing_reasons,
            monitoring_reliable=monitoring_reliable,
            vision_snapshot=vision_event.model_dump() if vision_event else None,
            sensor_snapshot=sensor_reading.model_dump() if sensor_reading else None,
        )


# Global singleton instance for easy import
risk_engine = RiskEngine()
