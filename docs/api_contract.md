# API Contract Specification

All endpoints are hosted by `backend/main.py` under the `/api/v1` namespace.

---

## 1. Monitoring & Vision Endpoints

### `POST /api/v1/monitoring/vision`
* **Description**: Ingests frame inference metrics from `ai_vision` pipeline or browser MediaPipe FaceMesh.
* **Request Body**: `VisionEventSchema`
  ```json
  {
    "timestamp": "2026-10-26T12:00:00.000Z",
    "face_detected": true,
    "eye_status": "CLOSED",
    "eye_closure_duration_ms": 1800.0,
    "yawn_detected": false,
    "head_nod_detected": false,
    "tracking_reliable": true,
    "ear_score": 0.19,
    "mar_score": 0.15
  }
  ```
* **Response (200 OK)**: `RiskStateSchema`

### `GET /api/v1/monitoring/status`
* **Description**: Returns consolidated telemetry for the frontend dashboard.
* **Response (200 OK)**:
  ```json
  {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "is_active": true,
    "trip_duration_seconds": 342.5,
    "risk_state": { "state": "NORMAL", "risk_score": 10.0, ... },
    "active_alert": null,
    "buzzer_status": "INACTIVE",
    "vision": { ... },
    "sensor": { "heart_rate_bpm": 74.0, "data_status": "SIMULATED_DEMO", ... },
    "gps": { "latitude": 12.9716, "longitude": 77.5946, "freshness_status": "LIVE", "permission_status": "GRANTED" },
    "escalation": {
      "stage": "NORMAL",
      "is_pending": false,
      "remaining_ack_seconds": 0.0,
      "last_sms_result": null,
      "sms_provider": "mock",
      "emergency_contact_phone": "+919876543210"
    }
  }
  ```

### `POST /api/v1/monitoring/session/start`
* **Query Params**: `driver_id` (string, default: `driver_default`)
* **Response (200 OK)**: `{"session_id": "...", "status": "ACTIVE", ...}`

### `POST /api/v1/monitoring/session/end`
* **Response (200 OK)**: `{"session_id": "...", "duration_seconds": 342.5, "status": "COMPLETED"}`

---

## 2. Sensor, Smartwatch, & Biometric Endpoints

### `POST /api/v1/sensors/smartwatch`
* **Request Body**: `SensorReadingSchema`
  Explicit `data_status` values: `CONNECTED_LIVE`, `CONNECTED_HISTORICAL`, `SIMULATED_DEMO`, `UNAVAILABLE`, `STALE_DATA`.
  ```json
  {
    "timestamp": "2026-10-26T12:00:00.000Z",
    "heart_rate_bpm": 74.0,
    "source": "boult_ble",
    "data_status": "CONNECTED_LIVE",
    "last_reading_timestamp": "2026-10-26T12:00:00.000Z",
    "device_battery_percent": 88.0,
    "connection_status": true
  }
  ```
* **Response (200 OK)**: `RiskStateSchema`

### `POST /api/v1/sensors/health_connect`
* **Description**: Mobile webhook accepting heart rate from Google Health Connect or Health Sync.
* **Payload**: `{"heart_rate_bpm": 74.0, "source": "google_health_connect"}`
* **Response (200 OK)**: `RiskStateSchema`

### `GET /api/v1/sensors/smartwatch/verify`
* **Description**: Returns vendor compatibility audit, GATT service inspection, and verification procedure.

### `POST /api/v1/sensors/gps`
* **Request Body**:
  ```json
  {
    "timestamp": "2026-10-26T12:00:00.000Z",
    "latitude": 12.9716,
    "longitude": 77.5946,
    "accuracy_m": 5.0,
    "speed_kmh": 45.0,
    "source": "android_http_webhook",
    "permission_status": "GRANTED"
  }
  ```
* **Response (200 OK)**: `{"status": "ACKNOWLEDGED", "gps": { ... }}`

### `GET /api/v1/sensors/gps`
* **Description**: Returns the latest verified vehicle location and freshness status.

### `GET /api/v1/sensors/network-info`
* **Description**: Returns host IP addresses and webhook URLs for Android phone integration.

---

## 3. Alerts & Emergency Endpoints

### `GET /api/v1/alerts/recent`
* **Query Params**: `limit` (int, default: 30)
* **Response (200 OK)**: Array of event log items.

### `POST /api/v1/alerts/sos`
* **Description**: Triggers immediate manual emergency SOS alert.
* **Response (200 OK)**: `AlertEventSchema`

### `POST /api/v1/alerts/acknowledge`
* **Description**: Silences active in-cabin buzzer and cancels pending family SMS escalation.
* **Response (200 OK)**: `{"status": "ACKNOWLEDGED", "action": "buzzer_silenced_and_sms_canceled"}`

### `POST /api/v1/alerts/contact`
* **Description**: Configures registered family contact number and name.
* **Request Body**: `{"phone_number": "+919876543210", "contact_name": "Primary Family Contact"}`

### `POST /api/v1/alerts/test-beep`
* **Description**: Emits a test tone through speakers to verify audio hardware.
