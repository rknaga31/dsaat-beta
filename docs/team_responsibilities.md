# Team Responsibilities & Ownership Matrix

This document outlines module ownership, deliverables, and expectations for all five team members.

---

## Member 1 — Frontend Engineer
* **Directory Ownership**: [`frontend/`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/frontend/)
* **Key Deliverables**:
  - React + Vite dashboard displaying real-time vehicle monitoring.
  - Viewfinder component displaying driver face bounding box and ocular metrics.
  - Risk state card with 0–100 score gauge and contributing factor bullet points.
  - Biometric card with heart rate (BPM), watch connection status, battery, and GPS coordinates.
  - Driver session controls (Start Trip / End Trip) and emergency manual SOS button.
  - Chronological event audit log table.
* **Integration Boundary**: Interacts exclusively with `backend` via REST API (`/api/v1/...`).

---

## Member 2 — AI and Computer Vision Engineer
* **Directory Ownership**: [`ai_vision/`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/ai_vision/)
* **Key Deliverables**:
  - Webcam capture pipeline with target FPS throttling (15–30 FPS).
  - MediaPipe FaceMesh landmark detection and 3D facial mesh extraction.
  - Eye Aspect Ratio (EAR) calculation and continuous eye-closure duration tracker.
  - Mouth Aspect Ratio (MAR) yawn detector differentiating speaking from fatigue yawning.
  - Head pose pitch estimation detecting micro-sleep downward nodding motions.
  - Packaging output into `VisionEventSchema` and dispatching to backend.
* **Integration Boundary**: Dispatches payloads conforming to `shared/schemas/vision_event.schema.json`.

---

## Member 3 — Backend and Risk Engine Engineer
* **Directory Ownership**: [`backend/`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/backend/)
* **Key Deliverables**:
  - FastAPI application structure, CORS middleware, lifespan events, and routing.
  - Pydantic schema validation enforcing non-zero missing telemetry rules.
  - Multimodal `RiskEngine` fusing vision and sensor telemetry into composite risk states (`NORMAL`, `WARNING`, `HIGH_RISK`, `MONITORING_UNAVAILABLE`).
  - `SessionManager` tracking driver trips, fatigue accumulation, and cached states.
  - `EventLogger` with in-memory ring buffer and persistent JSONL disk audit trail.
* **Integration Boundary**: Core broker connecting all 5 modules.

---

## Member 4 — Smartwatch and GPS Integration Engineer
* **Directory Ownership**: [`device_integration/`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/device_integration/)
* **Key Deliverables**:
  - Investigating physical Boult smartwatch BLE GATT compatibility (Service `0x180D`, Characteristic `0x2A37`).
  - Implementing honest `BoultSmartwatchAdapter` that returns `UNAVAILABLE` and `None` for BPM if hardware is disconnected (never fake live data).
  - Implementing `SimulatedSensorAdapter` with reproducible scenarios (`normal`, `drowsy_bradycardia`, `distress_tachycardia`, `disconnected`) clearly marked `SIMULATED`.
  - Planning and implementing Android GPS bridge (local Wi-Fi HTTP POST webhook or Termux).
* **Integration Boundary**: Dispatches biometric payloads to `POST /api/v1/sensors/smartwatch` and GPS coordinates to `POST /api/v1/sensors/gps`.

---

## Member 5 — Alerts, Family SOS, and Testing Engineer
* **Directory Ownership**: [`alerts_sos/`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/alerts_sos/)
* **Key Deliverables**:
  - Acoustic buzzer manager (`BeepManager`) with frequency escalation and rate-limiting.
  - State escalation manager implementing alert tiers (`WARNING` -> buzzer only; `HIGH_RISK` -> buzzer + family SMS).
  - Anti-spam cooldown logic preventing duplicate SMS dispatches to emergency contacts within 120s.
  - Emergency family SMS formatter creating Google Maps coordinates link (`https://maps.google.com/?q=...`).
  - Safe `MockSMSProvider` validating numbers and recording dispatches in memory.
  - Comprehensive unit test suite (`pytest`) covering escalation and duplicate prevention.
* **Integration Boundary**: Consumes `RiskStateSchema` updates from `backend` and triggers audio/SMS actions.
