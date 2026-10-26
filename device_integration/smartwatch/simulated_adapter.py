"""
Simulated Sensor Adapter.
Provides explicitly labelled synthetic biometric test data for development,
demos, and continuous testing without physical smartwatch hardware.
"""

import math
import time
from datetime import datetime, timezone
from typing import Optional
from backend.schemas.sensor_schema import SensorReadingSchema
from shared.constants import SensorDataStatusEnum
from device_integration.smartwatch.base_adapter import BaseSensorAdapter


class SimulatedSensorAdapter(BaseSensorAdapter):
    """
    Generates synthetic heart rate telemetry clearly stamped as SIMULATED.
    Supports injecting specific physiological scenarios for testing.
    """

    def __init__(self, scenario: str = "normal"):
        self.scenario = scenario
        self._connected = True
        self._step = 0
        self._last_reading_time = datetime.now(timezone.utc).isoformat()

    def set_scenario(self, scenario: str) -> None:
        """
        Switches test scenario:
        - 'normal': Stable 70-76 bpm resting heart rate.
        - 'drowsy_bradycardia': Dips to 46-52 bpm, simulating deep fatigue.
        - 'distress_tachycardia': Spikes to 118-130 bpm, simulating acute panic.
        - 'disconnected': Simulates peripheral communication failure.
        """
        valid_scenarios = ["normal", "drowsy_bradycardia", "distress_tachycardia", "disconnected", "stale"]
        if scenario not in valid_scenarios:
            raise ValueError(f"Unknown scenario '{scenario}'. Allowed: {valid_scenarios}")
        self.scenario = scenario

    def connect(self) -> bool:
        self._connected = True
        return True

    def read_sensor_data(self) -> SensorReadingSchema:
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()

        if not self._connected or self.scenario == "disconnected":
            return SensorReadingSchema(
                timestamp=now_iso,
                heart_rate_bpm=None,  # Missing values MUST be None
                source="simulated",
                data_status=SensorDataStatusEnum.UNAVAILABLE,
                last_reading_timestamp=self._last_reading_time,
                device_battery_percent=None,
                connection_status=False,
                data_freshness_seconds=None,
                error_state="Simulated sensor disconnected or peripheral unavailable.",
            )

        if self.scenario == "stale":
            # Simulate stale packet sampled 25 seconds ago
            stale_dt = datetime.fromtimestamp(now.timestamp() - 25.0, tz=timezone.utc)
            stale_iso = stale_dt.isoformat()
            return SensorReadingSchema(
                timestamp=stale_iso,
                heart_rate_bpm=72.0,
                source="simulated",
                data_status=SensorDataStatusEnum.STALE_DATA,
                last_reading_timestamp=stale_iso,
                device_battery_percent=85.0,
                connection_status=True,
                data_freshness_seconds=25.0,
                error_state="Simulated biometric reading is stale (>10s old).",
            )

        self._step += 1
        self._last_reading_time = now_iso

        # Calculate BPM based on selected scenario
        if self.scenario == "normal":
            # Gentle sinusoidal wave between 70 and 76 bpm
            bpm = 73.0 + 3.0 * math.sin(self._step * 0.2)
        elif self.scenario == "drowsy_bradycardia":
            # Dips below 50 bpm
            bpm = 48.0 + 2.0 * math.sin(self._step * 0.15)
        elif self.scenario == "distress_tachycardia":
            # Spikes above 115 bpm
            bpm = 120.0 + 4.0 * math.sin(self._step * 0.25)
        else:
            bpm = 72.0

        return SensorReadingSchema(
            timestamp=now_iso,
            heart_rate_bpm=round(bpm, 1),
            source="simulated",
            data_status=SensorDataStatusEnum.SIMULATED_DEMO,  # Explicitly SIMULATED_DEMO
            last_reading_timestamp=self._last_reading_time,
            device_battery_percent=85.0,
            connection_status=True,
            data_freshness_seconds=0.0,
            error_state="Synthetic demo telemetry active (Zero-hardware mode).",
        )

    def disconnect(self) -> None:
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected and self.scenario != "disconnected"
