"""
Smartwatch Integration Package.
"""

from device_integration.smartwatch.base_adapter import BaseSensorAdapter
from device_integration.smartwatch.boult_adapter import BoultSmartwatchAdapter
from device_integration.smartwatch.simulated_adapter import SimulatedSensorAdapter

__all__ = [
    "BaseSensorAdapter",
    "BoultSmartwatchAdapter",
    "SimulatedSensorAdapter",
]
