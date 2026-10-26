# Device Integration Module (`device_integration/`)

**Module Owner:** Member 4 — Smartwatch & GPS Integration Engineer

---

## 1. Module Responsibility

The `device_integration/` module manages peripheral telemetry inputs:
1. **Biometric Sensors (Smartwatch)**: Extracting real-time heart rate (BPM) to detect physiological relaxation (bradycardia) or acute panic/distress.
2. **Geographical Positioning (Android GPS)**: Ingesting live coordinates from the driver's smartphone to attach to emergency SOS messages.

---

## 2. Directory Structure

```text
device_integration/
├── README.md               # This specification
├── smartwatch/
│   ├── README.md           # Smartwatch constraints & BLE GATT documentation
│   ├── base_adapter.py     # Abstract Base Class BaseSensorAdapter
│   ├── boult_adapter.py    # Honest BLE adapter with safe UNAVAILABLE state
│   └── simulated_adapter.py# Explicitly labelled SIMULATED telemetry generator
├── android_gps/
│   ├── README.md           # Android GPS bridge specification
│   ├── location_schema.py  # Pydantic GPS schema
│   └── integration_notes.md# Step-by-step setup for Wi-Fi HTTP / Termux bridge
└── tests/
    └── test_adapters.py    # Unit tests for adapters and location validation
```

---

## 3. Critical Architecture Rules

* **No Faking Live Data**: If a Boult watch is not paired or lacks BLE GATT support, the system returns `UNAVAILABLE` and `None` for BPM. Never output synthetic data labeled as `LIVE`.
* **Never Substitute Zero for Missing Data**: Heart rate cannot be 0. Disconnected sensors must emit `None` (`null` in JSON).
* **Network Isolation**: The backend expects GPS telemetry delivered to `POST /api/v1/sensors/gps`.

---

## 4. Running Tests

```bash
pytest device_integration/tests/ -v
```
