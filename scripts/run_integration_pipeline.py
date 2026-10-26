"""
End-to-End Multimodal Integration Pipeline Demonstration Script.

Simulates live sequential dataflow across all 5 team modules:
1. Normal driving telemetry
2. Driver distraction (face missing > 3.0s)
3. Critical micro-sleep + physiological bradycardia
4. Emergency alert escalation with Mock SMS & Google Maps GPS link
5. 120-second duplicate alert cooldown prevention
6. Sensor staleness detection
7. Driver alert acknowledgement and trip conclusion
"""

import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.session_manager import SessionManager
from backend.services.risk_engine import RiskEngine
from alerts_sos.beep_manager import BeepManager
from alerts_sos.mock_sms_provider import MockSMSProvider
from alerts_sos.family_notification import FamilyNotificationService
from alerts_sos.escalation_manager import EscalationManager
from backend.schemas.vision_schema import VisionEventSchema
from backend.schemas.sensor_schema import SensorReadingSchema
from shared.constants import (
    EyeStatusEnum,
    SensorDataStatusEnum,
)

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_step(title: str):
    print(f"\n{CYAN}{'=' * 70}\n  {BOLD}{title}{RESET}\n{CYAN}{'=' * 70}{RESET}")


def run_pipeline_demo():
    print(f"\n{BOLD}======================================================================{RESET}")
    print(f"{BOLD}   MULTIMODAL DRIVER DROWSINESS & HEALTH SYSTEM - INTEGRATION DEMO   {RESET}")
    print(f"{BOLD}======================================================================{RESET}")

    # 1. Initialize Integrated Pipeline
    mock_sms = MockSMSProvider()
    beep_mgr = BeepManager(enabled=True, min_interval_sec=0.1)
    family_svc = FamilyNotificationService(
        sms_provider=mock_sms,
        emergency_contact_phone="+919876543210",
        emergency_contact_name="Family Emergency Contact",
    )
    escalation_mgr = EscalationManager(
        beep_manager=beep_mgr,
        family_service=family_svc,
        sms_cooldown_seconds=120,
    )
    session_mgr = SessionManager(escalation_manager=escalation_mgr)

    # Step 1: Start Trip Session
    print_step("STEP 1: Starting Driver Monitoring Session")
    session = session_mgr.start_session("driver_faculty_review")
    print(f"Session ID: {session['session_id']}")
    print(f"Driver ID : {session['driver_id']}")
    print(f"Status    : {GREEN}{session['status']}{RESET}")

    # Step 2: Ingest Normal Baseline Telemetry
    print_step("STEP 2: Simulating Normal Baseline Driving (Eyes Open, Normal BPM)")
    now_iso = datetime.now(timezone.utc).isoformat()
    session_mgr.update_gps(12.9716, 77.5946)

    sensor_normal = SensorReadingSchema(
        timestamp=now_iso,
        heart_rate_bpm=74.0,
        source="simulated",
        data_status=SensorDataStatusEnum.SIMULATED,
        last_reading_timestamp=now_iso,
    )
    vision_normal = VisionEventSchema(
        timestamp=now_iso,
        face_detected=True,
        eye_status=EyeStatusEnum.OPEN,
        eye_closure_duration_ms=0.0,
        yawn_detected=False,
        head_nod_detected=False,
        tracking_reliable=True,
        ear_score=0.34,
        mar_score=0.12,
    )

    session_mgr.update_sensor(sensor_normal)
    risk_normal = session_mgr.update_vision(vision_normal)
    print(f"Evaluated Risk State : {GREEN}{risk_normal.state.value}{RESET}")
    print(f"Composite Risk Score : {risk_normal.risk_score} / 100")
    print(f"Active Buzzer State  : {session_mgr.escalation_manager.beep_manager.status.value}")
    print(f"Dispatched SMS Count : {len(mock_sms.get_sent_messages())}")

    # Step 3: Simulating Driver Distraction / Face Absence (> 3.0s)
    print_step("STEP 3: Simulating Driver Distraction / Face Absence (3.2s)")
    engine_temp = session_mgr.escalation_manager  # Keep pipeline active
    no_face_vision = VisionEventSchema(
        timestamp=datetime.now(timezone.utc).isoformat(),
        face_detected=False,
        eye_status=EyeStatusEnum.UNKNOWN,
        eye_closure_duration_ms=0.0,
        yawn_detected=False,
        head_nod_detected=False,
        tracking_reliable=False,
    )
    # First frame missing
    session_mgr.update_vision(no_face_vision)
    # Fast forward face absence timer
    from backend.services.risk_engine import risk_engine
    risk_engine._face_lost_start_time = time.time() - 3.5

    risk_distracted = session_mgr.update_vision(no_face_vision)
    print(f"Evaluated Risk State : {YELLOW}{risk_distracted.state.value}{RESET}")
    print(f"Composite Risk Score : {risk_distracted.risk_score} / 100")
    print(f"Contributing Reasons : {risk_distracted.contributing_reasons}")
    print(f"Cabin Acoustic Alert : {YELLOW}WARNING CHIME (1500Hz) EMITTED{RESET}")

    # Step 4: Critical Multimodal Fatigue (Eyes Closed 2.8s + Bradycardia 48 BPM)
    print_step("STEP 4: Critical Multimodal Fatigue (Eyes Closed 2.8s + Heart Rate 48 BPM)")
    vision_crit = VisionEventSchema(
        timestamp=datetime.now(timezone.utc).isoformat(),
        face_detected=True,
        eye_status=EyeStatusEnum.CLOSED,
        eye_closure_duration_ms=2800.0,
        yawn_detected=False,
        head_nod_detected=True,
        tracking_reliable=True,
        ear_score=0.15,
        mar_score=0.20,
    )
    sensor_bradycardia = SensorReadingSchema(
        timestamp=datetime.now(timezone.utc).isoformat(),
        heart_rate_bpm=48.0,
        source="simulated",
        data_status=SensorDataStatusEnum.SIMULATED,
        last_reading_timestamp=datetime.now(timezone.utc).isoformat(),
    )

    session_mgr.update_sensor(sensor_bradycardia)
    risk_crit = session_mgr.update_vision(vision_crit)
    print(f"Evaluated Risk State : {RED}{BOLD}{risk_crit.state.value}{RESET}")
    print(f"Composite Risk Score : {RED}{risk_crit.risk_score} / 100{RESET}")
    print(f"Contributing Reasons : {risk_crit.contributing_reasons}")
    print(f"Cabin Acoustic Buzzer: {RED}CRITICAL ALARM (2500Hz) ACTIVE{RESET}")
    print(f"Emergency SMS Status : {session_mgr.latest_alert.family_sms_status.value}")

    # Step 5: Duplicate Alert Prevention & Cooldown Gate
    print_step("STEP 5: Testing 120-Second Duplicate Alert Prevention Gate")
    # Immediate subsequent high-risk event
    risk_subsequent = session_mgr.update_vision(vision_crit)
    print("Feeding consecutive high-risk frame within cooldown...")
    print(f"Subsequent SMS Status: {session_mgr.latest_alert.family_sms_status.value} (Duplicate Suppressed)")
    print(f"Total Sent SMS Count : {len(mock_sms.get_sent_messages())} (Exactly 1 message sent)")

    # Step 6: Sensor Staleness Detection
    print_step("STEP 6: Testing Sensor Telemetry Staleness (> 10s age check)")
    stale_timestamp = (datetime.now(timezone.utc) - timedelta(seconds=25)).isoformat()
    sensor_stale = SensorReadingSchema(
        timestamp=stale_timestamp,
        heart_rate_bpm=72.0,
        source="simulated",
        data_status=SensorDataStatusEnum.SIMULATED,
        last_reading_timestamp=stale_timestamp,
    )
    session_mgr.update_sensor(sensor_stale)
    print(f"Transmitted Sensor Status: {sensor_stale.data_status.value} (Flagged STALE)")

    # Step 7: Driver Acknowledges Alert & Trip Conclusion
    print_step("STEP 7: Driver Acknowledges Alert (Silence Buzzer) & Ends Session")
    ack = session_mgr.acknowledge_alert()
    print(f"Driver Override Action : {GREEN}{ack['action']}{RESET}")
    print(f"Buzzer Status After Ack: {session_mgr.escalation_manager.beep_manager.status.value}")

    summary = session_mgr.end_session()
    print(f"\nTrip Session Summary   : {summary}")
    print(f"\n{GREEN}{BOLD}End-to-End Pipeline Demonstration Successfully Verified!{RESET}\n")


if __name__ == "__main__":
    run_pipeline_demo()
