"""
Beep Manager.
Manages audible in-cabin acoustic alert tones with frequency escalation,
rate-limiting, duplicate prevention, and monitoring-unavailable warnings.
"""

import logging
import platform
import threading
import time
from typing import Optional, Union
from shared.constants import AlertLevelEnum, BeepStatusEnum

logger = logging.getLogger("beep_manager")

IS_WINDOWS = platform.system() == "Windows"
if IS_WINDOWS:
    try:
        import winsound
    except ImportError:
        winsound = None
else:
    winsound = None


class BeepManager:
    """Controls cabin audio alerts with frequency escalation and rate-limiting."""

    def __init__(self, enabled: bool = True, min_interval_sec: float = 1.0):
        self.enabled = enabled
        self.min_interval_sec = min_interval_sec
        self._last_beep_time: float = 0.0
        self._status = BeepStatusEnum.INACTIVE
        self._active_level: Optional[str] = None
        self._lock = threading.Lock()

    @property
    def status(self) -> BeepStatusEnum:
        return self._status

    @property
    def active_level(self) -> Optional[str]:
        return self._active_level

    @property
    def is_active(self) -> bool:
        return self._status == BeepStatusEnum.ACTIVE

    def play_warning(
        self,
        level: Union[AlertLevelEnum, str] = AlertLevelEnum.WARNING,
    ) -> BeepStatusEnum:
        """
        Emits an audible alert tone appropriate for the given severity tier:
        - WARNING: Moderate cautionary tone (1500 Hz, 300 ms)
        - CRITICAL: High-pitched urgent escalation alarm (2500 Hz, 500 ms)
        - MONITORING_UNAVAILABLE / INFO: Low cautionary chime (800 Hz, 250 ms)
        """
        if not self.enabled:
            self._status = BeepStatusEnum.MUTED
            return self._status

        level_str = level.value if isinstance(level, AlertLevelEnum) else str(level)
        now = time.time()

        with self._lock:
            # Enforce cooldown / rate-limiting to prevent buzzing freezes and duplicate overlapping threads
            if now - self._last_beep_time < self.min_interval_sec:
                return self._status
            self._last_beep_time = now
            self._active_level = level_str

        # Execute tone in background daemon thread to avoid blocking risk engine
        thread = threading.Thread(
            target=self._emit_tone,
            args=(level_str,),
            daemon=True,
        )
        thread.start()
        self._status = BeepStatusEnum.ACTIVE
        return self._status

    def play_monitoring_unavailable(self) -> BeepStatusEnum:
        """Warning tone emitted when camera or sensors become blocked / unavailable."""
        return self.play_warning("MONITORING_UNAVAILABLE")

    def _emit_tone(self, level_str: str):
        """Worker thread emitting hardware tone with frequency escalation."""
        try:
            if level_str in (AlertLevelEnum.CRITICAL.value, "CRITICAL"):
                freq = 2500
                duration_ms = 500
            elif level_str in (AlertLevelEnum.WARNING.value, "WARNING"):
                freq = 1500
                duration_ms = 300
            elif level_str in ("MONITORING_UNAVAILABLE", AlertLevelEnum.INFO.value, "INFO"):
                freq = 800
                duration_ms = 250
            else:
                freq = 1200
                duration_ms = 300

            if IS_WINDOWS and winsound:
                winsound.Beep(freq, duration_ms)
            else:
                # Terminal bell character fallback for non-Windows / headless environments
                print("\a", end="", flush=True)

            logger.info("Audible alert tone emitted: %s (%dHz for %dms)", level_str, freq, duration_ms)
        except Exception as exc:
            logger.debug("Audio hardware output issue: %s", exc)
            self._status = BeepStatusEnum.FAILED

    def stop_warning(self) -> BeepStatusEnum:
        """Silences the buzzer for graceful recovery or driver acknowledgement."""
        with self._lock:
            self._status = BeepStatusEnum.INACTIVE
            self._active_level = None
        logger.info("Audible cabin alert silenced.")
        return self._status
