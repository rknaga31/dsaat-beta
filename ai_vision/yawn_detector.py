"""
Yawn Detector.
Calculates Mouth Aspect Ratio (MAR) and differentiates normal speech from sustained yawning.
"""

import math
import time
from typing import List, Dict, Tuple, Optional
from ai_vision.face_landmark_detector import (
    LIPS_INNER_TOP,
    LIPS_INNER_BOTTOM,
    LIPS_CORNER_LEFT,
    LIPS_CORNER_RIGHT,
)


def _euclidean_dist(p1: Dict[str, float], p2: Dict[str, float]) -> float:
    return math.sqrt((p1["x"] - p2["x"]) ** 2 + (p1["y"] - p2["y"]) ** 2)


def calculate_mar(landmarks: List[Dict[str, float]]) -> float:
    """
    Computes Mouth Aspect Ratio (MAR) using inner vermillion border points:
    MAR = |lip_top - lip_bottom| / |lip_left - lip_right|
    """
    if len(landmarks) <= max(LIPS_INNER_TOP, LIPS_INNER_BOTTOM, LIPS_CORNER_LEFT, LIPS_CORNER_RIGHT):
        return 0.0

    top = landmarks[LIPS_INNER_TOP]
    bottom = landmarks[LIPS_INNER_BOTTOM]
    left = landmarks[LIPS_CORNER_LEFT]
    right = landmarks[LIPS_CORNER_RIGHT]

    vertical = _euclidean_dist(top, bottom)
    horizontal = _euclidean_dist(left, right)

    if horizontal == 0:
        return 0.0

    return vertical / horizontal


class YawnDetector:
    """Monitors sustained mouth opening indicative of drowsy yawning."""

    def __init__(self, mar_threshold: float = 0.55, min_yawn_duration_ms: float = 1800.0):
        self.mar_threshold = mar_threshold
        self.min_yawn_duration_ms = min_yawn_duration_ms
        self._yawn_start_time: Optional[float] = None

    def process_landmarks(
        self, landmarks: Optional[List[Dict[str, float]]], timestamp_sec: Optional[float] = None
    ) -> Tuple[bool, float]:
        """
        Analyzes mouth geometry and returns:
        (yawn_detected: bool, current_mar_score: float)
        """
        current_time = timestamp_sec if timestamp_sec is not None else time.time()

        if not landmarks or len(landmarks) < 400:
            self._yawn_start_time = None
            return False, 0.0

        mar = calculate_mar(landmarks)

        if mar >= self.mar_threshold:
            if self._yawn_start_time is None:
                self._yawn_start_time = current_time
            duration_ms = (current_time - self._yawn_start_time) * 1000.0
            if duration_ms >= self.min_yawn_duration_ms:
                return True, round(mar, 3)
        else:
            self._yawn_start_time = None

        return False, round(mar, 3)

    def reset(self):
        """Resets yawn tracking timers."""
        self._yawn_start_time = None
