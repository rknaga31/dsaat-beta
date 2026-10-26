# Faculty Evaluation Presentation & Defense Guide

This document equips the five team members to present the project confidently during academic evaluation and defend technical design decisions.

---

## 1. Project Thesis & Core Innovation

> **Question from Faculty: "Why is a multimodal approach necessary? Isn't a webcam alone sufficient to detect drowsiness?"**

* **Webcam-Only Vulnerabilities**:
  - In real-world driving, computer vision struggles with variable cabin lighting (night driving, glare, shadows) and occlusions (sunglasses, driver turning head, hands blocking face).
  - A camera can only observe external behavioral symptoms (eye closure, yawns), which occur *after* fatigue has set in.
* **Smartwatch-Only Vulnerabilities**:
  - Photoplethysmography (PPG) heart rate sensors have latency; a micro-sleep event can happen in 2.5 seconds, while physiological heart rate drops occur over tens of seconds.
* **The Multimodal Advantage**:
  - Combining immediate facial geometry ($EAR$, $MAR$, Head Pose) with continuous physiological metrics (bradycardia/tachycardia) provides a cross-validated, fail-safe safety score. If camera tracking degrades, the biometric stream maintains vigilance; if heart rate is steady, ocular tracking catches sudden acute micro-sleeps.

---

## 2. Five Member Presentation Speaking Roles

### Member 1: Frontend & Human-Machine Interface (HMI)
* **What to Show**: The React + Vite glassmorphism dashboard running at `http://localhost:5173`.
* **Talking Points**:
  - Decoupled architecture: The UI thread polls clean JSON telemetry (`GET /monitoring/status`) and is never blocked by video inference.
  - Cognitive ergonomics: Color-coded gauges (green = normal, yellow = warning, pulsating red = critical), real-time trip timer, and one-touch buzzer silence override.

### Member 2: Computer Vision & AI Inference
* **What to Show**: `ai_vision/` landmark pipeline, EAR and MAR mathematical calculations.
* **Talking Points**:
  - Uses 478 MediaPipe 3D face mesh topological points.
  - Demonstrates temporal duration tracking rather than single-frame classification, filtering out normal 150ms blinks while flagging sustained $\ge 1500\text{ms}$ closures.
  - Explains the automatic camera recovery mechanism on frame drops.

### Member 3: Backend & Multimodal Risk Fusion
* **What to Show**: FastAPI OpenAPI Swagger documentation (`http://127.0.0.1:8000/docs`) and `RiskEngine.evaluate_risk()`.
* **Talking Points**:
  - Demonstrates strict Pydantic contract validation (ISO-8601 timestamps, rejecting 0 BPM).
  - Explains sensor freshness validation: timestamps older than 10s transition to `STALE` and are safely ignored.
  - Explains temporal distraction tracking: missing face for $\ge 3.0\text{s}$ triggers a distraction warning.

### Member 4: Smartwatch & GPS Integration
* **What to Show**: `device_integration/` adapters and Android GPS bridge specification.
* **Talking Points**:
  - Honest engineering appraisal of Boult smartwatches: Boult uses proprietary Realtek/JL BLE chipsets syncing to vendor apps (`Boult Fit` / `Da Fit`) without public developer APIs.
  - Implemented BLE GATT Heart Rate Service (`0x180D`) with honest `UNAVAILABLE` fallback (never faking live data).
  - Outlines the local Wi-Fi HTTP POST Webhook bridging Android smartphone GPS to the backend laptop.

### Member 5: Safety Alerts, Family SOS, & Testing
* **What to Show**: Terminal showing `MockSMSProvider` output with Google Maps link, and `pytest -v` results.
* **Talking Points**:
  - Explains the two-tier escalation model (`WARNING` = buzzer only; `HIGH_RISK` = buzzer + family SMS).
  - Explains the **120-second cooldown window** preventing emergency contact inbox flooding.
  - Highlights the 28 passing automated unit and integration tests covering normal, boundary, and failure scenarios.

---

## 3. Anticipated Faculty Defense Q&A

### Q1: "Why did you use mock SMS instead of sending real SMS to the examiner's phone?"
> **Answer**: "We designed the system with a pluggable `BaseSMSProvider` abstract interface. By default, `SMS_PROVIDER=mock` ensures that continuous testing and code execution never incur carrier charges or fail due to external network outages during grading. For production evaluation, switching `.env` to `SMS_PROVIDER=twilio` or `fast2sms` with active API keys immediately dispatches live carrier SMS without any code modifications."

### Q2: "What happens if the driver's phone loses GPS satellite lock in a tunnel?"
> **Answer**: "The `FamilyNotificationService` and `location_schema.py` explicitly handle null GPS fixes. Instead of throwing a NullPointerException or aborting the SOS alert, the system formats the emergency text as `Vehicle Location: GPS signal unavailable` and still dispatches the alert immediately."

### Q3: "What prevents false alarms from short blinks or talking?"
> **Answer**: "Normal blinks take 100 to 200 ms. Our `EyeClosureDetector` uses a temporal sliding duration counter: only closures exceeding 1500 ms trigger a warning, and only closures exceeding 2500 ms trigger a critical alert. Similarly, conversational speech only causes brief spikes in Mouth Aspect Ratio (MAR), whereas our `YawnDetector` requires sustained opening $\ge 1800\text{ ms}$ before classifying a yawn."
