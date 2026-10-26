# Multimodal Driver Drowsiness and Health Monitoring System
## End-to-End System Architecture Specification

---

## 1. High-Level Modular Architecture

The system implements a decoupled, five-tier architecture ensuring strict separation of concerns, deterministic data flow, and independent team module development.

```mermaid
graph TD
    subgraph Tier1 [Tier 1: Physical Acquisition & Sensor Adapters]
        CAM[Driver Facing Camera Index 0] -->|Raw 720p/1080p BGR Frames| CM[ai_vision: CameraManager]
        WATCH[Smartwatch Biometric Sensor] -->|BLE GATT / Simulation| SA[device_integration: BaseSensorAdapter]
        PHONE[Android Smartphone Bridge] -->|Wi-Fi HTTP / Termux| GPS_BRIDGE[device_integration: GPS Bridge]
    end

    subgraph Tier2 [Tier 2: Perception & Temporal Feature Extraction]
        CM -->|Frame 15 FPS| FD[FaceLandmarkDetector MediaPipe 478 Mesh]
        FD -->|Eye Contours| ED[EyeClosureDetector EAR Temporal Tracker]
        FD -->|Lip Contours| YD[YawnDetector MAR Temporal Tracker]
        FD -->|3D Nose Chin Points| HP[HeadPoseEstimator PnP Pitch Tracker]
        
        ED -->|Ocular Metrics| VS[VisionService Orchestrator]
        YD -->|Yawn Metrics| VS
        HP -->|Nod Metrics| VS
        VS -->|Validated VisionEventSchema JSON| DISPATCH_V[HTTP POST /monitoring/vision]
    end

    subgraph Tier3 [Tier 3: Ingestion, Validation & Multimodal Risk Engine]
        DISPATCH_V --> API[FastAPI Gateway api/v1]
        SA -->|Validated SensorReadingSchema| DISPATCH_S[HTTP POST /sensors/smartwatch] --> API
        GPS_BRIDGE -->|Validated GPSLocationSchema| DISPATCH_G[HTTP POST /sensors/gps] --> API
        
        API --> SM[SessionManager Trip Context]
        SM --> RE[Multimodal RiskEngine]
        
        subgraph RiskFusion [Deterministic Fusion & Staleness Engine]
            RE -->|10s Freshness Check| FRESH[Sensor Freshness Filter]
            RE -->|3.0s Absence Tracker| DISTRACT[Distraction / Face Absence Filter]
            RE -->|EAR < 0.21 for >= 2.5s| CRIT_EYE[Critical Eye Closure Metric]
            RE -->|BPM < 50 or > 115| BIO_METRIC[Physiological Distress Metric]
        end
        
        RE -->|Emits RiskStateSchema| SM
        SM --> LOG[EventLogger RAM Ring Buffer + JSONL Disk Audit]
    end

    subgraph Tier4 [Tier 4: Safety Escalation & Actuation]
        SM --> EM[alerts_sos: EscalationManager]
        EM -->|Debounce & Cooldown Check| FILTER[120s SMS Anti-Spam Gate]
        
        EM -->|WARNING Tone: 1500Hz 300ms| BUZZ_WARN[Acoustic Buzzer Chime]
        EM -->|CRITICAL Tone: 2500Hz 600ms| BUZZ_CRIT[Urgent Danger Buzzer]
        
        FILTER -->|Dispatches with GPS Hyperlink| NOTIF[FamilyNotificationService]
        NOTIF -->|MockSMSProvider / Twilio| SMS_DISPATCH[Emergency Contact Mobile]
    end

    subgraph Tier5 [Tier 5: Presentation & Dashboard Visualization]
        SM -->|GET /monitoring/status 1.5s Poll| CLIENT[frontend: React 18 + Vite]
        CLIENT --> DASH_HUD[Viewfinder HUD & Bounding Mesh]
        CLIENT --> DASH_GAUGE[Composite Risk Score Gauge 0-100]
        CLIENT --> DASH_BIO[Heart Rate BPM & Sensor Provenance]
        CLIENT --> DASH_ALERT[Emergency Banner & Silence Override]
        CLIENT --> DASH_AUDIT[Live Event Audit History Log]
    end
```

---

## 2. End-to-End Pipeline Stages

### Stage 1: Physical Acquisition & Temporal Feature Extraction
* **Frame Acquisition**: Handled by `CameraManager` at 15 FPS with rate-throttling. If frame reads drop consecutive frames (> 5), an automatic hardware reconnection handler executes without crashing the process.
* **Topological Facial Landmarks**: Extracted via MediaPipe FaceMesh (478 topological vertices).
* **Temporal Ocular Analysis**:
  $$EAR = \frac{||p_2 - p_6|| + ||p_3 - p_5||}{2 \cdot ||p_1 - p_4||}$$
  Continuous eyelid closure duration is measured in milliseconds. If $EAR < 0.21$ continuously for $\ge 1500\text{ ms}$, it flags moderate drowsiness; if $\ge 2500\text{ ms}$, it flags critical micro-sleep.
* **Temporal Yawn Analysis**:
  $$MAR = \frac{||p_{\text{top}} - p_{\text{bottom}}||}{||p_{\text{left}} - p_{\text{right}}||}$$
  Differentiates short conversational speech phonemes from sustained physiological yawning ($\ge 1800\text{ ms}$).
* **Head Pose Estimation**: Approximate 3D Pitch angle relative to baseline upright posture detects downward head nodding.

### Stage 2: Biometric & Geographical Telemetry Ingestion
* **Biometric Telemetry**: Ingested via `BaseSensorAdapter`. If physical hardware is disconnected, the adapter outputs `UNAVAILABLE` and `None` for BPM. **Missing readings are never represented as 0**.
* **GPS Telemetry**: Ingested via Android HTTP bridge or simulated position coordinates into `GPSLocationSchema`.

### Stage 3: Multimodal Fusion & Temporal Staleness Engine
* **Freshness Verification**: If `sensor_reading.timestamp` is older than `10.0 seconds`, the data status transitions to `STALE` and the reading is ignored to prevent stale data from biasing the safety score.
* **Missing-Face Distraction Tracking**: If the driver's face is missing for $\ge 3.0\text{ seconds}$ while driving, the system raises a `WARNING` state for distraction/occlusion.
* **Multimodal Score Fusion**: The `RiskEngine` calculates a normalized composite risk score ($0.0 \text{ to } 100.0$) and categorizes the vehicle into:
  - `NORMAL` (Score < 40.0)
  - `WARNING` (Score 40.0 – 79.9)
  - `HIGH_RISK` (Score $\ge 80.0$)
  - `MONITORING_UNAVAILABLE` (Telemetry degraded or unreadable)

### Stage 4: Alert Escalation & Anti-Spam Gate
* **Tier 1 (`WARNING`)**: Acoustic chime (1500 Hz, 300 ms) warns driver. Family SMS is withheld to prevent false alarms.
* **Tier 2 (`HIGH_RISK`)**: High-pitch acoustic buzzer (2500 Hz, 600 ms) sounds continuously. Emergency SMS with driver identity, incident rationale, and Google Maps GPS coordinates is dispatched.
* **120-Second Cooldown**: Prevents spamming emergency contacts during sustained incidents.
* **Manual Override**: The driver can acknowledge the alert via the dashboard or API to mute the buzzer.

### Stage 5: Real-Time Visualization
* The React dashboard polls `GET /api/v1/monitoring/status` every 1.5 seconds, visualizing telemetry without running computer vision inference inside the browser DOM.
