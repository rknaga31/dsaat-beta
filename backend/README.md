# Backend and Risk Engine Module (`backend/`)

**Module Owner:** Member 3 — Backend and Risk Engine Engineer

---

## 1. Module Responsibility

The `backend/` service acts as the central integration brain of the Multimodal Driver Drowsiness and Health Monitoring System. It is responsible for:
1. **API Endpoints**: Hosting high-performance FastAPI REST routes for frontend dashboards, AI vision streams, and device sensor telemetry.
2. **Data Validation**: Enforcing strict Pydantic model compliance adhering to shared JSON schemas (ISO-8601 timestamps, explicit `SIMULATED` vs `LIVE` provenance, rejecting invalid zero heart rates).
3. **Multimodal Risk Classification**: Executing the `RiskEngine` to fuse ocular closure, yawning, head nods, and heart rate telemetry into composite scores (`NORMAL`, `WARNING`, `HIGH_RISK`, `MONITORING_UNAVAILABLE`).
4. **Session Management**: Tracking driver trips, fatigue accumulation over driving duration, and telemetry snapshots.
5. **Event Logging**: In-memory ring buffer and persistent JSONL disk auditing for safety reviews and alerts.

---

## 2. Directory Structure

```text
backend/
├── README.md               # This specification
├── main.py                 # FastAPI application entry point
├── api/
│   ├── routes.py           # Master /api/v1 router
│   ├── monitoring.py       # Vision feed ingestion & driver trip session endpoints
│   ├── sensors.py          # Smartwatch & GPS telemetry endpoints
│   └── alerts.py           # Alert retrieval, manual SOS, buzzer acknowledgement
├── config/
│   └── settings.py         # Environment variables & runtime settings
├── models/
│   └── database.py         # Trip session and driver entity data models
├── schemas/
│   ├── vision_schema.py    # Pydantic schema for vision events
│   ├── sensor_schema.py    # Pydantic schema for biometric sensor events
│   ├── risk_schema.py      # Pydantic schema for calculated risk states
│   └── alert_schema.py     # Pydantic schema for alert/SOS events
├── services/
│   ├── risk_engine.py      # Core multimodal fusion risk algorithm
│   ├── event_logger.py     # Chronological event ring buffer & audit logger
│   └── session_manager.py  # Session lifecycle & cached telemetry state
└── tests/
    └── test_risk_engine.py # Unit tests for risk logic and data validation
```

---

## 3. Interfaces & Contracts

* **Inputs**:
  - AI Vision frames via `POST /api/v1/monitoring/vision` (`VisionEventSchema`)
  - Smartwatch biometrics via `POST /api/v1/sensors/smartwatch` (`SensorReadingSchema`)
  - GPS coordinates via `POST /api/v1/sensors/gps`
  - Manual SOS trigger via `POST /api/v1/alerts/sos`
* **Outputs**:
  - `RiskStateSchema` (emitted on every telemetry update)
  - Full system status via `GET /api/v1/monitoring/status`
  - Historical events via `GET /api/v1/alerts/recent`

---

## 4. Running the Backend Locally

Ensure the root virtual environment has the required dependencies installed:

```bash
pip install -r requirements.txt
```

Launch the FastAPI development server with hot-reload:

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Interactive OpenAPI documentation is automatically available at:
* Swagger UI: `http://127.0.0.1:8000/docs`
* ReDoc: `http://127.0.0.1:8000/redoc`

---

## 5. Running Backend Tests

```bash
pytest backend/tests/ -v
```
