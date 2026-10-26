# End-to-End Multimodal Data-Flow Specification

This document details the exact sequence and transformations of data packets as they travel through the system.

---

## 1. Sequence & Data-Flow Diagram

```mermaid
sequenceDiagram
    autonumber
    participant HW as Hardware (Cam / BLE / GPS)
    participant CV as ai_vision (VisionService)
    participant BIO as device_integration
    participant API as backend (FastAPI Gateway)
    participant SM as SessionManager & RiskEngine
    participant AL as alerts_sos (EscalationManager)
    participant UI as frontend (React Dashboard)

    %% Step 1: Physical Acquisition & Inference
    HW->>CV: Video Frame (15 FPS BGR Matrix)
    CV->>CV: FaceLandmarkDetector (478 Points)
    CV->>CV: Temporal EAR, MAR & Head Pose Calculation
    CV->>API: HTTP POST /api/v1/monitoring/vision (VisionEventSchema)

    %% Step 2: Biometric Ingestion
    HW->>BIO: Smartwatch Heart Rate Telemetry
    BIO->>BIO: Validates Sensor Data & Provenance
    BIO->>API: HTTP POST /api/v1/sensors/smartwatch (SensorReadingSchema)

    %% Step 3: Risk Evaluation
    API->>SM: Passes validated payloads
    SM->>SM: RiskEngine.evaluate_risk()
    Note over SM: Checks sensor freshness (age < 10s)<br/>Checks face absence duration (< 3.0s)<br/>Fuses ocular & cardiac distress metrics
    SM-->>API: Returns RiskStateSchema (NORMAL / WARNING / HIGH_RISK)

    %% Step 4: Alert Escalation
    SM->>AL: EscalationManager.process_risk_update()
    alt State is WARNING
        AL->>AL: BeepManager.play_warning(1500Hz)
        Note over AL: In-cabin chime sounds; NO SMS sent
    else State is HIGH_RISK
        AL->>AL: BeepManager.play_warning(2500Hz)
        AL->>AL: Check 120s SMS Cooldown
        alt Cooldown Expired
            AL->>HW: MockSMSProvider: Dispatches SMS + Google Maps Link
        else Within Cooldown
            Note over AL: Duplicate SMS suppressed
        end
    end

    %% Step 5: Dashboard Presentation
    UI->>API: HTTP GET /api/v1/monitoring/status (every 1.5s)
    API-->>UI: Full status (Risk, Vision, Biometrics, GPS, Active Alert)
    UI->>UI: Renders HUD, Gauge, BPM, and Emergency Banner
```

---

## 2. Packet Schemas & Transformations

### Packet 1: Raw Physical Input to `VisionEventSchema`
* **Producer**: `ai_vision.vision_service`
* **Target**: `POST /api/v1/monitoring/vision`
* **JSON Payload**:
  ```json
  {
    "timestamp": "2026-10-26T12:00:00.000Z",
    "face_detected": true,
    "eye_status": "CLOSED",
    "eye_closure_duration_ms": 2800.0,
    "yawn_detected": false,
    "head_nod_detected": true,
    "tracking_reliable": true,
    "ear_score": 0.17,
    "mar_score": 0.22
  }
  ```
* **Data-Quality Indicators**: `tracking_reliable` (bool), `face_detected` (bool).
* **Failure State**: If camera disconnected, returns `face_detected: false`, `tracking_reliable: false`, `eye_status: "UNKNOWN"`.

---

### Packet 2: Biometric Ingestion to `SensorReadingSchema`
* **Producer**: `device_integration.smartwatch`
* **Target**: `POST /api/v1/sensors/smartwatch`
* **JSON Payload**:
  ```json
  {
    "timestamp": "2026-10-26T12:00:00.000Z",
    "heart_rate_bpm": 48.0,
    "source": "simulated",
    "data_status": "SIMULATED",
    "last_reading_timestamp": "2026-10-26T12:00:00.000Z",
    "device_battery_percent": 85.0
  }
  ```
* **Data-Quality Indicators**: `data_status` (`LIVE`, `SIMULATED`, `STALE`, `UNAVAILABLE`).
* **Failure State**: If watch unpaired, `heart_rate_bpm: null`, `data_status: "UNAVAILABLE"` (never 0). If timestamp > 10s old, transitions to `"STALE"`.

---

### Packet 3: Multimodal Fusion Output to `RiskStateSchema`
* **Producer**: `backend.services.risk_engine`
* **Target**: `backend.services.session_manager` & `alerts_sos.escalation_manager`
* **JSON Payload**:
  ```json
  {
    "timestamp": "2026-10-26T12:00:00.000Z",
    "state": "HIGH_RISK",
    "risk_score": 90.0,
    "contributing_reasons": [
      "Critical eye closure: eyes closed for 2.8s",
      "Drowsy head nod movement detected",
      "Low heart rate (48 bpm) indicates potential drowsiness/bradycardia"
    ],
    "monitoring_reliable": true
  }
  ```

---

### Packet 4: Safety Escalation to `AlertEventSchema` & Emergency SMS
* **Producer**: `alerts_sos.escalation_manager`
* **Action**: In-cabin tone via `BeepManager` + SMS dispatch via `FamilyNotificationService`.
* **SMS Output Format**:
  ```text
  EMERGENCY ALERT: Driver Primary Driver detected in severe drowsiness / medical distress!
  Reason: Critical eye closure: eyes closed for 2.8s; Low heart rate (48 bpm)
  Vehicle Location: https://maps.google.com/?q=12.97160,77.59460
  ```
