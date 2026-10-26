"""
Unit tests for Device Integration adapters and schemas.
"""

import pytest
from datetime import datetime, timezone
from device_integration.smartwatch.simulated_adapter import SimulatedSensorAdapter
from device_integration.smartwatch.boult_adapter import BoultSmartwatchAdapter
from device_integration.android_gps.location_schema import GPSLocationSchema
from shared.constants import SensorDataStatusEnum


def test_simulated_adapter_normal():
    adapter = SimulatedSensorAdapter(scenario="normal")
    sample = adapter.read_sensor_data()
    assert sample.source == "simulated"
    assert sample.data_status == SensorDataStatusEnum.SIMULATED
    assert sample.heart_rate_bpm is not None
    assert 68.0 <= sample.heart_rate_bpm <= 80.0


def test_simulated_adapter_drowsy_bradycardia():
    adapter = SimulatedSensorAdapter(scenario="drowsy_bradycardia")
    sample = adapter.read_sensor_data()
    assert sample.heart_rate_bpm is not None
    assert sample.heart_rate_bpm < 55.0


def test_simulated_adapter_disconnected_state():
    adapter = SimulatedSensorAdapter(scenario="disconnected")
    sample = adapter.read_sensor_data()
    assert sample.heart_rate_bpm is None
    assert sample.data_status == SensorDataStatusEnum.UNAVAILABLE


def test_boult_adapter_disconnected_safety():
    adapter = BoultSmartwatchAdapter(mac_address="00:00:00:00:00:00")
    sample = adapter.read_sensor_data()
    # Must report UNAVAILABLE and None for BPM
    assert sample.source == "boult_ble"
    assert sample.data_status == SensorDataStatusEnum.UNAVAILABLE
    assert sample.heart_rate_bpm is None


def test_gps_location_schema_valid():
    now_iso = datetime.now(timezone.utc).isoformat()
    loc = GPSLocationSchema(
        timestamp=now_iso,
        latitude=12.9716,
        longitude=77.5946,
        speed_kmh=55.0,
        accuracy_m=3.5,
    )
    assert loc.latitude == 12.9716
    assert loc.longitude == 77.5946
    assert loc.is_valid is True
