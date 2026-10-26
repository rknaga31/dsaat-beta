# Individual Contribution Records & Team Division

This document records the specific module ownership, technical contributions, authored files, and test coverage for each of the five team members.

---

## Member 1 — Frontend & Human-Machine Interface Engineer
* **Assigned Module**: [`frontend/`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/frontend/)
* **Files Authored**:
  - [`frontend/src/pages/Dashboard.jsx`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/frontend/src/pages/Dashboard.jsx): Master responsive layout coordinating UI sub-cards and trip lifecycle.
  - [`frontend/src/components/CameraFeed.jsx`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/frontend/src/components/CameraFeed.jsx): Viewfinder HUD overlay displaying bounding box, eye status, EAR, and MAR metrics.
  - [`frontend/src/components/RiskCard.jsx`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/frontend/src/components/RiskCard.jsx): Composite risk score gauge (0–100) and rationale bullet points.
  - [`frontend/src/components/SensorCard.jsx`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/frontend/src/components/SensorCard.jsx): Biometric display (Heart Rate BPM, device status, battery, GPS).
  - [`frontend/src/components/AlertBanner.jsx`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/frontend/src/components/AlertBanner.jsx): Warning / danger alerts and buzzer silence button.
  - [`frontend/src/components/EventHistory.jsx`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/frontend/src/components/EventHistory.jsx): Chronological safety audit table.
  - [`frontend/src/hooks/useMonitoring.js`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/frontend/src/hooks/useMonitoring.js): Non-blocking telemetry polling hook with offline fallback.
  - [`frontend/src/services/apiClient.js`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/frontend/src/services/apiClient.js): Fetch client interacting with backend REST endpoints.
* **Test Verification**: UI rendering and build verification via `npm run build`.

---

## Member 2 — AI & Computer Vision Engineer
* **Assigned Module**: [`ai_vision/`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/ai_vision/)
* **Files Authored**:
  - [`ai_vision/camera_manager.py`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/ai_vision/camera_manager.py): VideoCapture hardware manager with 15 FPS throttle and consecutive-failure auto-recovery.
  - [`ai_vision/face_landmark_detector.py`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/ai_vision/face_landmark_detector.py): MediaPipe FaceMesh topological point extractor (478 vertices).
  - [`ai_vision/eye_closure_detector.py`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/ai_vision/eye_closure_detector.py): Ocular aperture math ($EAR$) and continuous duration timer (ms).
  - [`ai_vision/yawn_detector.py`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/ai_vision/yawn_detector.py): Mouth Aspect Ratio ($MAR$) calculating sustained yawning vs conversational speech.
  - [`ai_vision/head_pose_estimator.py`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/ai_vision/head_pose_estimator.py): 3D head pitch calculation detecting micro-sleep downward nods.
  - [`ai_vision/vision_service.py`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/ai_vision/vision_service.py): Master inference orchestrator packaging `VisionEventSchema`.
* **Test Verification**: [`ai_vision/tests/test_vision_service.py`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/ai_vision/tests/test_vision_service.py) (4 automated tests).

---

## Member 3 — Backend & Multimodal Risk Engine Engineer
* **Assigned Module**: [`backend/`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/backend/)
* **Files Authored**:
  - [`backend/main.py`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/backend/main.py): FastAPI application gateway with CORS, health routes, and graceful lifespan hooks.
  - [`backend/services/risk_engine.py`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/backend/services/risk_engine.py): Multimodal fusion algorithm fusing vision, heart rate, sensor staleness (>10s), and face-missing distraction (>3.0s).
  - [`backend/services/session_manager.py`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/backend/services/session_manager.py): Trip duration tracker orchestrating risk engine and alert escalation.
  - [`backend/services/event_logger.py`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/backend/services/event_logger.py): Chronological ring buffer and JSONL disk persistence.
  - [`backend/schemas/`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/backend/schemas/): Pydantic data models enforcing contracts and physiological boundary limits ($30 \le \text{BPM} \le 240$).
  - [`backend/api/`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/backend/api/): REST routes (`/monitoring`, `/sensors`, `/alerts`).
* **Test Verification**: [`backend/tests/test_risk_engine.py`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/backend/tests/test_risk_engine.py) (6 tests) and [`backend/tests/test_end_to_end_integration.py`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/backend/tests/test_end_to_end_integration.py) (3 tests).

---

## Member 4 — Smartwatch & GPS Integration Engineer
* **Assigned Module**: [`device_integration/`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/device_integration/)
* **Files Authored**:
  - [`device_integration/smartwatch/base_adapter.py`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/device_integration/smartwatch/base_adapter.py): Abstract base class for biometric sensor adapters.
  - [`device_integration/smartwatch/boult_adapter.py`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/device_integration/smartwatch/boult_adapter.py): BLE GATT Heart Rate Service (`0x180D`) driver with honest `UNAVAILABLE` fallback.
  - [`device_integration/smartwatch/simulated_adapter.py`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/device_integration/smartwatch/simulated_adapter.py): Realistic scenario generator (`normal`, `drowsy_bradycardia`, `distress_tachycardia`, `disconnected`) with explicit `SIMULATED` markers.
  - [`device_integration/android_gps/location_schema.py`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/device_integration/android_gps/location_schema.py): WGS84 GPS coordinate schema.
  - [`device_integration/android_gps/integration_notes.md`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/device_integration/android_gps/integration_notes.md): Wi-Fi HTTP POST Webhook and Termux bridge guide.
* **Test Verification**: [`device_integration/tests/test_adapters.py`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/device_integration/tests/test_adapters.py) (5 automated tests).

---

## Member 5 — Alerts, Family SOS, & Testing Engineer
* **Assigned Module**: [`alerts_sos/`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/alerts_sos/)
* **Files Authored**:
  - [`alerts_sos/beep_manager.py`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/alerts_sos/beep_manager.py): Non-blocking acoustic warning buzzer with frequency escalation (`1500Hz` vs `2500Hz`).
  - [`alerts_sos/escalation_manager.py`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/alerts_sos/escalation_manager.py): State escalation engine enforcing the **120-second duplicate alert cooldown**.
  - [`alerts_sos/family_notification.py`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/alerts_sos/family_notification.py): Emergency message formatter generating Google Maps GPS hyperlinks (`https://maps.google.com/?q=...`).
  - [`alerts_sos/sms_provider.py`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/alerts_sos/sms_provider.py): Pluggable provider interface supporting Mock, Twilio, and Fast2SMS.
  - [`alerts_sos/mock_sms_provider.py`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/alerts_sos/mock_sms_provider.py): Safe test sender validating E.164 phone numbers and recording dispatches in memory.
  - [`backend/tests/test_robustness_and_errors.py`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/backend/tests/test_robustness_and_errors.py): Suite of 6 robustness, boundary, staleness, and exception tests.
* **Test Verification**: [`alerts_sos/tests/test_escalation.py`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/alerts_sos/tests/test_escalation.py) (4 tests) and integration test suite.
