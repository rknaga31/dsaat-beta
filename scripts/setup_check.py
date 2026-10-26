"""
Multimodal Driver Drowsiness and Health Monitoring System
Setup & Integrity Verification Script.

Validates environment, folder structure, starter files, JSON schemas,
syntax, and package imports across all 5 team modules.
"""

import sys
import os
import json
import py_compile
from pathlib import Path

# Add project root to sys.path so modules can be imported
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Color / Symbol formatting
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"


def print_header(title: str):
    print(f"\n{CYAN}{'=' * 65}\n  {title}\n{'=' * 65}{RESET}")


def check_python_version() -> bool:
    print(f"Checking Python version... ", end="")
    major, minor = sys.version_info[:2]
    if (major, minor) >= (3, 10):
        print(f"{GREEN}[PASS]{RESET} (Python {major}.{minor}.{sys.version_info.micro})")
        return True
    else:
        print(f"{RED}[FAIL]{RESET} Python 3.10+ required; found {major}.{minor}")
        return False


def check_directory_structure() -> bool:
    print_header("1. Verifying Team Folder & Directory Layout")
    required_dirs = [
        "frontend/src/components",
        "frontend/src/pages",
        "frontend/src/services",
        "frontend/src/hooks",
        "frontend/src/types",
        "frontend/public",
        "ai_vision/tests",
        "backend/api",
        "backend/models",
        "backend/schemas",
        "backend/services",
        "backend/config",
        "backend/tests",
        "device_integration/smartwatch",
        "device_integration/android_gps",
        "device_integration/tests",
        "alerts_sos/tests",
        "shared/schemas",
        "docs",
        "scripts",
    ]

    all_ok = True
    for rel_path in required_dirs:
        dir_path = PROJECT_ROOT / rel_path
        if dir_path.is_dir():
            print(f"  {GREEN}[OK]{RESET} {rel_path}/")
        else:
            print(f"  {RED}[X] MISSING DIRECTORY:{RESET} {rel_path}/")
            all_ok = False
    return all_ok


def check_starter_files() -> bool:
    print_header("2. Verifying Starter Files & Module Boundaries")
    required_files = [
        "README.md",
        ".gitignore",
        ".env.example",
        "requirements.txt",
        "package.json",
        "shared/constants.py",
        "shared/schemas/vision_event.schema.json",
        "shared/schemas/sensor_reading.schema.json",
        "shared/schemas/risk_state.schema.json",
        "shared/schemas/alert_event.schema.json",
        "backend/main.py",
        "backend/api/routes.py",
        "backend/api/monitoring.py",
        "backend/api/sensors.py",
        "backend/api/alerts.py",
        "backend/schemas/vision_schema.py",
        "backend/schemas/sensor_schema.py",
        "backend/schemas/risk_schema.py",
        "backend/services/risk_engine.py",
        "backend/services/event_logger.py",
        "backend/services/session_manager.py",
        "ai_vision/camera_manager.py",
        "ai_vision/face_landmark_detector.py",
        "ai_vision/eye_closure_detector.py",
        "ai_vision/yawn_detector.py",
        "ai_vision/head_pose_estimator.py",
        "ai_vision/vision_service.py",
        "device_integration/smartwatch/base_adapter.py",
        "device_integration/smartwatch/boult_adapter.py",
        "device_integration/smartwatch/simulated_adapter.py",
        "device_integration/android_gps/location_schema.py",
        "alerts_sos/beep_manager.py",
        "alerts_sos/escalation_manager.py",
        "alerts_sos/sms_provider.py",
        "alerts_sos/mock_sms_provider.py",
        "alerts_sos/family_notification.py",
        "frontend/src/App.jsx",
        "frontend/src/main.jsx",
        "frontend/src/index.css",
        "frontend/package.json",
        "docs/architecture.md",
        "docs/api_contract.md",
        "docs/setup_guide.md",
        "docs/team_responsibilities.md",
        "docs/review2_demo_checklist.md",
        "docs/end_to_end_dataflow.md",
        "docs/feature_completion_matrix.md",
        "docs/error_handling_and_robustness.md",
        "docs/individual_contributions.md",
        "docs/faculty_presentation_guide.md",
        "docs/google_health_smartwatch_guide.md",
        "scripts/run_integration_pipeline.py",
        "scripts/run_live_camera.py",
    ]

    all_ok = True
    for rel_path in required_files:
        file_path = PROJECT_ROOT / rel_path
        if file_path.is_file():
            print(f"  {GREEN}[OK]{RESET} {rel_path}")
        else:
            print(f"  {RED}[X] MISSING FILE:{RESET} {rel_path}")
            all_ok = False
    return all_ok


def check_json_schemas() -> bool:
    print_header("3. Validating JSON Schemas")
    schema_dir = PROJECT_ROOT / "shared" / "schemas"
    schemas = [
        "vision_event.schema.json",
        "sensor_reading.schema.json",
        "risk_state.schema.json",
        "alert_event.schema.json",
    ]

    try:
        import jsonschema
        has_jsonschema = True
    except ImportError:
        has_jsonschema = False
        print(f"  {YELLOW}Note: jsonschema library not installed; validating JSON syntax only.{RESET}")

    all_ok = True
    for s_name in schemas:
        s_path = schema_dir / s_name
        try:
            with open(s_path, "r", encoding="utf-8") as f:
                schema_data = json.load(f)
            if has_jsonschema:
                jsonschema.Draft7Validator.check_schema(schema_data)
            print(f"  {GREEN}[OK]{RESET} {s_name} (valid Draft-07 JSON Schema)")
        except Exception as exc:
            print(f"  {RED}[X] Schema error in {s_name}:{RESET} {exc}")
            all_ok = False
    return all_ok


def check_python_syntax() -> bool:
    print_header("4. Verifying Python File Syntax")
    py_files = list(PROJECT_ROOT.glob("**/*.py"))
    all_ok = True
    for py_file in py_files:
        if ".venv" in py_file.parts or "node_modules" in py_file.parts:
            continue
        try:
            py_compile.compile(str(py_file), doraise=True)
            rel_name = py_file.relative_to(PROJECT_ROOT)
            print(f"  {GREEN}[OK]{RESET} {rel_name}")
        except py_compile.PyCompileError as err:
            print(f"  {RED}[X] Syntax Error in {py_file}:{RESET}\n    {err}")
            all_ok = False
    return all_ok


def check_module_imports() -> bool:
    print_header("5. Verifying Python Module Imports & Inter-Module Interfaces")
    imports_to_test = [
        ("shared.constants", ["RiskStateEnum", "AlertLevelEnum", "EyeStatusEnum"]),
        ("backend.schemas", ["VisionEventSchema", "SensorReadingSchema", "RiskStateSchema"]),
        ("backend.services.risk_engine", ["RiskEngine", "risk_engine"]),
        ("backend.services.event_logger", ["EventLogger", "event_logger"]),
        ("backend.services.session_manager", ["SessionManager", "session_manager"]),
        ("ai_vision.eye_closure_detector", ["EyeClosureDetector", "calculate_ear"]),
        ("ai_vision.yawn_detector", ["YawnDetector", "calculate_mar"]),
        ("ai_vision.head_pose_estimator", ["HeadPoseEstimator"]),
        ("device_integration.smartwatch.simulated_adapter", ["SimulatedSensorAdapter"]),
        ("device_integration.smartwatch.boult_adapter", ["BoultSmartwatchAdapter"]),
        ("device_integration.android_gps.location_schema", ["GPSLocationSchema"]),
        ("alerts_sos.beep_manager", ["BeepManager"]),
        ("alerts_sos.mock_sms_provider", ["MockSMSProvider"]),
        ("alerts_sos.family_notification", ["FamilyNotificationService"]),
        ("alerts_sos.escalation_manager", ["EscalationManager"]),
    ]

    all_ok = True
    for mod_name, symbols in imports_to_test:
        try:
            mod = __import__(mod_name, fromlist=symbols)
            for sym in symbols:
                if not hasattr(mod, sym):
                    raise AttributeError(f"Module {mod_name} missing symbol {sym}")
            print(f"  {GREEN}[OK]{RESET} Imported {mod_name} ({', '.join(symbols)})")
        except Exception as exc:
            print(f"  {RED}[X] Import failed for {mod_name}:{RESET} {exc}")
            all_ok = False
    return all_ok


def main():
    print(f"\n{CYAN}Starting Setup and System Scaffolding Verification Check...{RESET}")
    v_ok = check_python_version()
    d_ok = check_directory_structure()
    f_ok = check_starter_files()
    s_ok = check_json_schemas()
    c_ok = check_python_syntax()
    i_ok = check_module_imports()

    passed = all([v_ok, d_ok, f_ok, s_ok, c_ok, i_ok])
    print_header("Summary of Results")
    if passed:
        print(f"{GREEN}ALL INTEGRITY CHECKS PASSED SUCCESSFULLY! (100% OK){RESET}")
        print("Each team member's module boundaries, schemas, and starter files are valid and ready.\n")
        sys.exit(0)
    else:
        print(f"{RED}ONE OR MORE INTEGRITY CHECKS FAILED.{RESET}")
        print("Please review the errors above and ensure all required dependencies are installed.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
