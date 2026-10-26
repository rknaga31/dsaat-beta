# Shared Contracts, Schemas, and Constants

This directory provides the authoritative, single-source-of-truth contracts for the **Multimodal AI-Based Driver Drowsiness and Health Monitoring System**.

All 5 sub-teams MUST import and conform to the definitions herein to guarantee smooth integration.

---

## 1. Directory Contents

* **`constants.py`**: Shared Python enums (`RiskStateEnum`, `AlertLevelEnum`, `SensorDataStatusEnum`, `EyeStatusEnum`, `BeepStatusEnum`, `SmsStatusEnum`, `LocationStatusEnum`) and default system thresholds.
* **`schemas/vision_event.schema.json`**: JSON Schema for AI vision inference frames.
* **`schemas/sensor_reading.schema.json`**: JSON Schema for smartwatch biometric telemetry.
* **`schemas/risk_state.schema.json`**: JSON Schema for fused multi-modal driver risk assessments.
* **`schemas/alert_event.schema.json`**: JSON Schema for audible chimes and emergency family SOS notifications.

---

## 2. Core Integration Rules

1. **Standard Timestamps**: All timestamps MUST be in **ISO-8601 UTC format** (e.g. `2026-10-26T12:00:00.000Z`).
2. **Never Use Zero for Missing Readings**: If a heart rate sensor is disconnected, reading unavailable, or unreadable, the value MUST be `None` / `null`. Never substitute `0` for missing values, as `0` indicates cardiac arrest in clinical logic.
3. **Honest Data Provenance**: If using dummy data or simulated values during local testing, the `data_status` MUST explicitly be `"SIMULATED"`. Never label simulated test streams as `"LIVE"`.
4. **Independent Evolution**: Teams may extend payloads with optional fields, but MUST NOT alter required contract fields without team consensus and updating this directory.

---

## 3. Python Usage Example

```python
from shared.constants import RiskStateEnum, AlertLevelEnum, SensorDataStatusEnum
# In backend, schemas/models can import these enums directly.
```
