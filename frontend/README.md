# Frontend Dashboard Module (`frontend/`)

**Module Owner:** Member 1 — Frontend Engineer

---

## 1. Module Responsibility

The `frontend/` module provides a state-of-the-art telemetry and driver safety dashboard:
1. **Live Camera Display & HUD**: Visualizing driver face lock, eye closure duration, EAR/MAR scores, and head-nod warnings.
2. **Multimodal Risk Card**: Displaying composite risk score (0–100 gauge), categorical state badges (`NORMAL`, `WARNING`, `HIGH_RISK`, `MONITORING_UNAVAILABLE`), and contributing rationale.
3. **Biometric Status Card**: Displaying real-time heart rate (BPM), peripheral connection status (`LIVE BLE`, `SIMULATED`, `UNAVAILABLE`), watch battery, and vehicle GPS fix.
4. **Trip Session Management**: Starting, monitoring, and concluding driving sessions.
5. **Emergency SOS Controls**: Manual driver panic button and acoustic buzzer silencing.
6. **Audit & Event History**: Viewing chronological logs of risk escalations and SMS dispatches.

---

## 2. Directory Structure

```text
frontend/
├── README.md               # This specification
├── package.json            # Vite + React dependencies & scripts
├── index.html              # HTML5 entrypoint
├── public/                 # Static assets & icons
└── src/
    ├── main.jsx            # React DOM mounting
    ├── App.jsx             # Top-level app layout
    ├── index.css           # Dark theme design system & glassmorphism styling
    ├── types/
    │   └── index.js        # Shared frontend enums & contract constants
    ├── services/
    │   └── apiClient.js    # Fetch API client for FastAPI backend
    ├── hooks/
    │   └── useMonitoring.js# Polling hook for real-time telemetry updates
    ├── pages/
    │   └── Dashboard.jsx   # Master responsive monitoring dashboard
    └── components/
        ├── AlertBanner.jsx # Warning & emergency alert notification header
        ├── CameraFeed.jsx  # Viewfinder HUD & ocular metrics meters
        ├── RiskCard.jsx    # Risk state gauge & contributing factors
        ├── SensorCard.jsx  # Heart rate BPM, battery & GPS coordinates
        └── EventHistory.jsx# Chronological safety audit table
```

---

## 3. Running Locally

Navigate to the `frontend/` directory and install dependencies:

```bash
cd frontend
npm install
npm run dev
```

The dashboard will launch at `http://localhost:5173`.
By default, it will communicate with the backend running at `http://127.0.0.1:8000/api/v1`.
If the backend is not running, the dashboard displays a non-blocking `Backend Offline` banner and retains UI responsiveness.
