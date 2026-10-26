# Review 2 Demo & Presentation Checklist

Use this checklist during academic project reviews to demonstrate the modularity and integration capabilities of the system.

---

## 1. Pre-Demo Verification Checklist

- [ ] Run `python scripts/setup_check.py` — verify all checks pass with zero errors.
- [ ] Run `pytest` — verify backend, vision, adapter, and alert tests pass cleanly.
- [ ] Confirm `.env` has `SMS_PROVIDER=mock` to avoid external API network errors.
- [ ] Confirm `SMARTWATCH_SOURCE=SIMULATED` (or paired BLE device if hardware is ready).
- [ ] Launch backend: `python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000`.
- [ ] Launch frontend: `cd frontend && npm run dev` (running on `http://localhost:5173`).

---

## 2. Review 2 Demo Script (Step-by-Step)

### Step 1: Architecture & Modularity Overview
* Show the 5 distinct folders matching the 5 team member assignments:
  - `frontend/` (Member 1)
  - `ai_vision/` (Member 2)
  - `backend/` (Member 3)
  - `device_integration/` (Member 4)
  - `alerts_sos/` (Member 5)
* Highlight `shared/` containing JSON schemas and enums, preventing circular dependencies.

### Step 2: Live Backend Health & OpenAPI Documentation
* Navigate to `http://127.0.0.1:8000/docs`.
* Show Swagger UI documenting `/monitoring`, `/sensors`, and `/alerts` endpoints.
* Execute `GET /health` to show healthy system status and active configuration.

### Step 3: Frontend Dashboard Walkthrough
* Navigate to `http://localhost:5173`.
* Demonstrate the glassmorphism UI, real-time polling indicator, and driver session timer.
* Click **"Start Trip"** to initialize driver session logging.

### Step 4: Scenario 1 — Normal Driving State
* Show baseline metrics:
  - Risk Score < 20 (State: `NORMAL`)
  - Eyes: `OPEN`, EAR > 0.30
  - Heart Rate: ~72 BPM (Status: `SIMULATED`)
  - No active buzzer or SMS alerts.

### Step 5: Scenario 2 — Warning Tier (Moderate Fatigue)
* Simulate eye closure of 1.8 seconds or sustained yawning.
* Observe immediate state transition:
  - Risk Score elevates to 50–65 (State: `WARNING`).
  - Warning banner appears on dashboard.
  - Short acoustic warning chime (1500 Hz) emitted.
  - Family SMS is **NOT** triggered (avoids false alarm).

### Step 6: Scenario 3 — Critical Emergency SOS Escalation
* Simulate critical eye closure (> 2.5 seconds) combined with low heart rate (< 50 BPM).
* Observe high-risk escalation:
  - Risk Score elevates > 80 (State: `HIGH_RISK`).
  - Pulsing critical danger banner appears on dashboard.
  - Urgent high-pitch buzzer (2500 Hz) activates.
  - **Emergency SMS dispatched** via `MockSMSProvider`.
  - Inspection of terminal output shows message containing driver details and Google Maps GPS link (`https://maps.google.com/?q=...`).

### Step 7: Scenario 4 — Anti-Spam Cooldown & Buzzer Muting
* Demonstrate that subsequent high-risk frames within 120 seconds **do not** flood the emergency contact with duplicate SMS messages.
* Click **"Silence Buzzer"** to demonstrate manual driver override and alert acknowledgement.
* Click **"End Trip"** to view session summary and recorded event history.
