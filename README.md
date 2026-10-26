# 🛡️ D-SAAT Beta: Driver Drowsiness & Health Monitoring System

> An intelligent, life-saving driver safety system that combines **AI Computer Vision**, **Smartwatch Vitals**, and **Smartphone GPS** to detect fatigue and prevent road accidents before they happen.

---

## 📌 About The Project (5 Core Sections)

Welcome to **D-SAAT Beta** (Driver Safety & Alertness Assessment Telemetry). Below is an easy-to-read, 5-section breakdown explaining the core concepts, how it works, and the technology behind it.

---

### Section 1: What is D-SAAT? (The Core Idea in Simple English)

Every year, thousands of road accidents happen simply because drivers fall asleep at the wheel. When driving for long hours or late at night, a driver can experience **"micro-sleeps"**—brief moments lasting only 2 to 3 seconds where their eyes close and their brain switches off. At highway speeds (100 km/h), a car travels nearly 80 meters completely uncontrolled in just 3 seconds!

Most existing anti-sleep devices use only a camera. But a camera alone can make mistakes:
- What if the driver is wearing sunglasses?
- What if the lighting inside the car is poor?
- What if the driver simply squints while looking at bright oncoming headlights?

**The D-SAAT Solution:**  
Instead of guessing from a camera alone, **D-SAAT uses multimodal fusion**—meaning it looks at **three different sources of truth at the same time**:
1. **The Driver's Face** (Is the driver closing their eyes or yawning?)
2. **The Driver's Body** (Is their heart rate dropping, indicating deep relaxation and drowsiness?)
3. **The Car's Location & Speed** (Is the vehicle moving on a road, or is it safely parked?)

By putting these three clues together, D-SAAT accurately measures driver alertness without annoying false alarms.

---

### Section 2: How It Works (Multimodal Fusion Explained Simply)

D-SAAT continuously evaluates safety through three smart layers and merges them in real time:

#### Layer 1: AI Computer Vision (The Eyes & Mouth)
- Uses an ultra-lightweight AI model (**MediaPipe FaceMesh**) directly in the browser.
- It tracks 468 landmark points on the driver's face at 30 frames per second.
- **Eye Aspect Ratio (EAR)**: Measures how open the eyelids are. If EAR drops below `0.21`, the eyes are closed. If they stay closed for more than 1.5 seconds, it flags an alert; if closed for 2.5 seconds, it flags critical sleep.
- **Mouth Aspect Ratio (MAR)**: Measures mouth height vs. width. When MAR exceeds `0.55`, it detects a fatigue yawn.
- **Head Nodding**: Tracks head pitch angle to detect when a drowsy driver's chin falls forward toward their chest.

#### Layer 2: Physiological Watch Telemetry (The Heart)
- Wearable watches measure heart rate (**BPM**) and Heart Rate Variability (**HRV**).
- When humans enter deep drowsiness, their autonomic nervous system shifts into parasympathetic dominance—causing **drowsy bradycardia** (heart rate dropping below 50 BPM).
- Under acute stress or panic, heart rate spikes (**tachycardia** > 115 BPM).
- D-SAAT checks data freshness: if watch data is older than 10 seconds, it gracefully treats it as stale and falls back to camera vision without crashing.

#### Layer 3: Vehicle Geolocation (The Android GPS)
- Tracks vehicle speed and precise latitude/longitude coordinates.
- If the driver closes their eyes while moving at 80 km/h, the urgency is maximum compared to a vehicle standing still in a parking spot.

#### The Multimodal Fusion Risk Engine
All three layers stream into a mathematical **Risk Engine** that calculates a unified score from `0` to `100`:
- **0 to 39 (NORMAL)**: Driver is attentive, eyes open, healthy resting heart rate (60–90 BPM).
- **40 to 79 (WARNING)**: Minor fatigue detected (frequent yawning, partial eye closure, or elevated fatigue markers).
- **80 to 100 (HIGH RISK)**: Severe emergency (sustained eye closure > 2.5s, head nodding, or bradycardia while moving).

---

### Section 3: Driver Safety Escalation (Beep Alarm & Family SOS)

When danger is detected, D-SAAT follows a strict **4-stage safety escalation workflow**:

```
[Normal Driving]
       │
       ▼
[Stage 1: Warning Detection]
       │ ──> Gentle 800 Hz cabin chime + amber visual alert
       ▼
[Stage 2: Critical Alarm Activated]
       │ ──> Loud 1500 Hz - 2500 Hz pulsating buzzer wakes driver up
       ▼
[Stage 3: 10-Second Grace Window Countdown]
       │ ──> Giant banner: "FAMILY SOS DISPATCHING IN 10s... TAP TO CANCEL"
       │
       ├───> Driver taps "I Am Awake" ──> Buzzer silences, SOS canceled
       │
       └───> Driver does NOT respond (unconscious / asleep)
               │
               ▼
[Stage 4: Autonomous Family SOS Dispatched]
       │ ──> Instant SMS delivered to family with live Google Maps pin
```

**Medically Responsible Notification**:  
The SMS message is formulated carefully without making false medical diagnosis claims:
> *"URGENT SAFETY ALERT: Driver Drowsiness System has detected sustained driver fatigue or lack of responsiveness. Immediate attention recommended. Current vehicle speed: 74 km/h. Live Map Location: https://maps.google.com/?q=12.9716,77.5946"*

---

### Section 4: Hardware & Real-World Integration

D-SAAT is designed for real-world hardware while being completely honest about device limitations:

1. **Boult Smartwatches & Budget Wearables**:
   - Budget consumer smartwatches (Boult Drift, Striker, Crown, Ridge) pair with proprietary mobile apps (Boult Fit / Da Fit) and do not provide an open cloud API.
   - D-SAAT includes a built-in **Compatibility Audit tool** that scans for Bluetooth SIG Heart Rate Service `0x180D`.
   - If direct BLE is locked, D-SAAT provides an open **Google Health Connect bridge** over local Wi-Fi, allowing any Android phone to forward heart rate telemetry to the system.
   - For demonstrations, a **Zero-Hardware Simulator** allows testing Normal (74 BPM), Drowsy (48 BPM), Panic (122 BPM), and Stale states with one tap.

2. **Android Phone GPS Bridge**:
   - Modern mobile Chrome blocks browser GPS on plain HTTP over local networks.
   - D-SAAT solves this by providing a lightweight HTTP webhook (`POST /api/v1/sensors/gps`). Android automation tools (such as **GPS Logger** or **MacroDroid**) can push real-time satellite coordinates directly over Wi-Fi without needing HTTPS.

3. **In-Cabin Audio Buzzer**:
   - Uses multi-frequency sound generation (800 Hz info chime, 1500 Hz fatigue tone, 2500 Hz high-pitch alarm) via the browser's native **Web Audio API** and a non-blocking daemon buzzer in Python.

---

### Section 5: Technologies Used & Quick Start Guide

D-SAAT is built using modern, fast, and production-tested technologies:

#### Core Technologies:
| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend Framework** | React 18 + Vite | Lightning-fast reactive user interface |
| **Styling** | Vanilla CSS Glassmorphism | Dark automotive cockpit design system |
| **Facial AI** | MediaPipe FaceMesh | 468-point 3D landmark tracking at 30 FPS |
| **Audio Engine** | Web Audio API | Frequency-shifting cabin buzzer alarms |
| **Backend API** | FastAPI + Python 3.11+ | High-throughput asynchronous REST gateway |
| **Data Integrity** | Pydantic v2 + JSON Schema | Strict boundary validation for medical & GPS data |
| **Notifications** | Twilio SMS + Mock Provider | Safe emergency alert delivery pipeline |

---

#### 🚀 Quick Start Guide (Run Locally in 2 Minutes)

##### 1. Clone the Repository
```bash
git clone https://github.com/rknaga31/dsaat-beta.git
cd dsaat-beta
```

##### 2. Start the Backend API Server
```bash
# Install Python dependencies
pip install -r requirements.txt

# Run the FastAPI server on port 8000
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
- Interactive API Documentation: **http://127.0.0.1:8000/docs**

##### 3. Start the Frontend Web Cockpit
In a new terminal window:
```bash
cd frontend

# Install Node dependencies
npm install

# Start Vite dev server on port 5173
npm run dev
```
- Open the Dashboard in your browser: **http://127.0.0.1:5173/**

##### 4. Running Automated Tests
```bash
python -m pytest -v
```
*(All 40 unit and end-to-end integration tests will run and pass).*

---

### 👨‍💻 Project Information & License
- **Project Name**: D-SAAT Beta (Driver Safety & Alertness Assessment Telemetry)
- **Author**: R Naga Abisheik ([@rknaga31](https://github.com/rknaga31))
- **License**: MIT Open Source License
