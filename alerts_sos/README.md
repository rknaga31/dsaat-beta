# Alerts, Family SOS, and Testing Module (`alerts_sos/`)

**Module Owner:** Member 5 — Alerts, Family SOS, and Testing Engineer

---

## 1. Module Responsibility

The `alerts_sos/` module is responsible for safety mitigation, acoustic alert chimes, and emergency family notifications:
1. **Audible In-Cabin Warnings**: Playing sound tones with frequency escalation using `BeepManager` (rate-limited, threaded, cross-platform with Windows `winsound` / terminal bell).
2. **Escalation Management**: Consuming fused `RiskState` updates and determining appropriate escalation actions (`NORMAL` -> `WARNING` -> `HIGH_RISK`).
3. **Anti-Spam & Duplicate Alert Prevention**: Enforcing cooldown windows (default 120s) so emergency contacts are not spammed with duplicate SMS messages during sustained high-risk events.
4. **Emergency SMS Dispatch**: Formatting emergency text messages containing driver identity, incident rationale, and Google Maps GPS coordinates (`family_notification.py`).
5. **Provider Interface & Mock Testing**: Providing `BaseSMSProvider` and `MockSMSProvider` to allow complete local simulation and verification without incurring external carrier costs or sending unintended messages.

---

## 2. Directory Structure

```text
alerts_sos/
├── README.md                   # This specification
├── beep_manager.py             # Acoustic buzzer controls with frequency escalation
├── escalation_manager.py       # Alert state machine, cooldowns & duplicate prevention
├── sms_provider.py             # Abstract SMS provider interface
├── mock_sms_provider.py        # Safe test sender validating numbers & logging locally
├── family_notification.py      # SOS message formatter with Google Maps coordinates link
└── tests/
    └── test_escalation.py      # Unit tests for alert tiers, cooldowns, and mock SMS
```

---

## 3. Escalation Tiers & Actions

| Evaluated Risk State | Cabin Buzzer | Emergency SMS to Family | Cooldown Applied |
| :--- | :--- | :--- | :--- |
| **`NORMAL`** | Silenced / INACTIVE | None | Resets alert state |
| **`WARNING`** | Short warning pulse (1500 Hz) | None (avoids false panic) | 1.0s audio rate limit |
| **`HIGH_RISK`** | Urgent critical pulse (2500 Hz) | **Dispatched with GPS Link** | **120 seconds** cooldown |
| **`MONITORING_UNAVAILABLE`**| Silenced | None | Logged to system audit |

---

## 4. Running the Tests

```bash
pytest alerts_sos/tests/ -v
```
