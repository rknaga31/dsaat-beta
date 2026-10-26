"""
Base Sensor Adapter Interface.
Defines abstract contracts for all physical and simulated biometric sensor adapters.
"""

from abc import ABC, abstractmethod
from typing import Optional
from backend.schemas.sensor_schema import SensorReadingSchema


class BaseSensorAdapter(ABC):
    """Abstract interface that every smartwatch/sensor provider must implement."""

    @abstractmethod
    def connect(self) -> bool:
        """
        Attempts to establish connection to the sensor device.
        Returns True if connection succeeded, False otherwise.
        """
        pass

    @abstractmethod
    def read_sensor_data(self) -> SensorReadingSchema:
        """
        Polls or reads the latest sample packet from the sensor.
        Must return a validated SensorReadingSchema.
        If reading is unavailable or device disconnected, heart_rate_bpm MUST be None
        and data_status MUST be UNAVAILABLE (never return 0 for missing data).
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Closes hardware connection and cleans up peripheral handles."""
        pass

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Returns True if the sensor is currently paired and responding."""
        pass

    @property
    def connection_status(self) -> bool:
        """Alias for is_connected."""
        return self.is_connected

    @property
    def error_state(self) -> Optional[str]:
        """Returns diagnostic error message or None if healthy."""
        return None
