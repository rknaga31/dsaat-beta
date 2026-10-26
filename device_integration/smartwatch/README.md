# Smartwatch Integration Sub-Module (`device_integration/smartwatch/`)

**Sub-Module Owner:** Member 4 — Smartwatch & GPS Integration Engineer

---

## 1. Overview & Constraints

This sub-module provides biometric telemetry (Heart Rate in BPM) to the backend risk engine.

### Hardware Reality Notice: Boult Smartwatch
* Boult consumer smartwatches (e.g., Boult Drift, Striker, Crown) communicate with proprietary apps (`Boult Fit`, `Da Fit`, `FitCloudPro`).
* **There is NO public developer cloud API or official SDK** for Boult smartwatches.
* Accessing real-time heart rate from the watch onto a development laptop requires direct Bluetooth Low Energy (BLE) GATT communication:
  * Service UUID: `0x180D` (Heart Rate)
  * Characteristic UUID: `0x2A37` (Heart Rate Measurement)
* If your physical Boult watch does not broadcast this standard BLE GATT characteristic or requires proprietary encryption tokens, **do not fake live data**. Fall back cleanly to `UNAVAILABLE` or use the `SimulatedSensorAdapter` for integration testing.

---

## 2. Adapters

1. **`base_adapter.py`**: Abstract base class (`BaseSensorAdapter`) declaring `connect()`, `read_sensor_data()`, `disconnect()`, and `is_connected`.
2. **`boult_adapter.py`**: BLE adapter implementing Bleak GATT scanning and decoding. Returns `data_status="UNAVAILABLE"` and `heart_rate_bpm=None` if hardware is unavailable.
3. **`simulated_adapter.py`**: Test generator providing reproducible scenarios (`normal`, `drowsy_bradycardia`, `distress_tachycardia`, `disconnected`) with explicit `data_status="SIMULATED"`.

---

## 3. Usage Example

```python
from device_integration.smartwatch.simulated_adapter import SimulatedSensorAdapter

adapter = SimulatedSensorAdapter(scenario="normal")
reading = adapter.read_sensor_data()
print("Heart rate:", reading.heart_rate_bpm, "Status:", reading.data_status)
```
