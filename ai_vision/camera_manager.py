"""
Camera Manager.
Handles webcam initialization, hardware capture, frame extraction,
automatic reconnection on failure, and safe thread/resource cleanup.
"""

import logging
import time
from typing import Optional, Tuple, Any

logger = logging.getLogger("camera_manager")

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    cv2 = None
    CV2_AVAILABLE = False


class CameraManager:
    """Manages video capture device lifecycle with automatic fault recovery."""

    def __init__(
        self,
        camera_index: int = 0,
        target_fps: int = 15,
        max_failures_before_reconnect: int = 5,
        reconnect_cooldown_sec: float = 2.0,
    ):
        self.camera_index = camera_index
        self.target_fps = target_fps
        self.frame_interval = 1.0 / max(target_fps, 1)
        self.cap: Optional[Any] = None
        self.is_running = False
        self._last_frame_time = 0.0

        # Fault tolerance and reconnection attributes
        self.consecutive_failures = 0
        self.max_failures_before_reconnect = max_failures_before_reconnect
        self.reconnect_cooldown_sec = reconnect_cooldown_sec
        self._last_reconnect_time = 0.0

    def start_camera(self) -> bool:
        """Initializes the physical webcam capture device."""
        if not CV2_AVAILABLE:
            logger.warning(
                "OpenCV (cv2) is not installed. Camera hardware cannot be opened. "
                "Install opencv-python via requirements.txt."
            )
            self.is_running = False
            return False

        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                logger.error(f"Unable to open camera index {self.camera_index}")
                self.is_running = False
                return False

            self.is_running = True
            self.consecutive_failures = 0
            logger.info(f"Camera {self.camera_index} initialized successfully at {self.target_fps} FPS.")
            return True
        except Exception as exc:
            logger.error(f"Error initializing camera: {exc}")
            self.is_running = False
            return False

    def read_frame(self) -> Tuple[bool, Optional[Any]]:
        """
        Captures a single frame from the camera, throttled to the target FPS.
        Automatically attempts device reconnection if consecutive frame reads fail.
        Returns: (success: bool, frame: np.ndarray or None)
        """
        if not self.is_running:
            return False, None

        if not self.cap:
            self.consecutive_failures += 1
            if self.consecutive_failures >= self.max_failures_before_reconnect:
                self._attempt_recovery()
            return False, None

        # Rate throttle
        now = time.time()
        elapsed = now - self._last_frame_time
        if elapsed < self.frame_interval:
            time.sleep(self.frame_interval - elapsed)

        try:
            ret, frame = self.cap.read()
            self._last_frame_time = time.time()

            if not ret or frame is None:
                self.consecutive_failures += 1
                logger.warning(f"Failed to grab frame (consecutive failures: {self.consecutive_failures}).")

                # Trigger recovery reconnection if threshold exceeded
                if self.consecutive_failures >= self.max_failures_before_reconnect:
                    self._attempt_recovery()

                return False, None

            # Frame read succeeded; reset failure counter
            self.consecutive_failures = 0
            return True, frame
        except Exception as exc:
            self.consecutive_failures += 1
            logger.error(f"Exception during camera read: {exc}")
            if self.consecutive_failures >= self.max_failures_before_reconnect:
                self._attempt_recovery()
            return False, None

    def _attempt_recovery(self):
        """Attempts to reinitialize the video capture handle after connection drop."""
        now = time.time()
        if now - self._last_reconnect_time < self.reconnect_cooldown_sec:
            return

        self._last_reconnect_time = now
        logger.info(f"Attempting camera hardware recovery on index {self.camera_index}...")

        try:
            if self.cap and CV2_AVAILABLE:
                self.cap.release()
        except Exception:
            pass

        self.cap = None
        self.start_camera()

    def stop_camera(self):
        """Releases the camera device and frees system resources."""
        if self.cap and CV2_AVAILABLE:
            try:
                self.cap.release()
            except Exception as exc:
                logger.error(f"Error releasing camera: {exc}")
        self.cap = None
        self.is_running = False
        self.consecutive_failures = 0
        logger.info("Camera device stopped.")
