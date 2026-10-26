"""
Eye Closure Detector.
Calculates Eye Aspect Ratio (EAR) and measures continuous eyelid closure duration.
"""

import math
import time
from typing import List, Dict, Tuple, Optional
from shared.constants import EyeStatusEnum
from ai_vision.face_landmark_detector import LEFT_EYE_INDICES, RIGHT_EYE_INDICES


def _euclidean_dist(p1: Dict[str, float], p2: Dict[str, float]) -> float:
    """Calculates 2D euclidean distance between two normalized coordinate points."""
    return math.sqrt((p1["x"] - p2["x"]) ** 2 + (p1["y"] - p2["y"]) ** 2)


def calculate_ear(landmarks: List[Dict[str, float]], eye_indices: List[int]) -> float:
    """
    Computes Eye Aspect Ratio (EAR) given 6 standard eye contour points:
    EAR = (|p2 - p6| + |p3 - p5|) / (2 * |p1 - p4|)
    """
    if len(landmarks) <= max(eye_indices):
        return 0.0

    p1 = landmarks[eye_indices[0]]
    p2 = landmarks[eye_indices[1]]
    p3 = landmarks[eye_indices[2]]
    p4 = landmarks[eye_indices[3]]
    p5 = landmarks[eye_indices[4]]
    p6 = landmarks[eye_indices[5]]

    vertical_1 = _euclidean_dist(p2, p6)
    vertical_2 = _euclidean_dist(p3, p5)
    horizontal = _euclidean_dist(p1, p4)

    if horizontal == 0:
        return 0.0

    return (vertical_1 + vertical_2) / (2.0 * horizontal)


class EyeClosureDetector:
    """Evaluates ocular aperture and monitors persistent closure duration."""

    def __init__(
        self,
        closed_ear_threshold: float = 0.21,
        partial_ear_threshold: float = 0.25,
    ):
        self.closed_ear_threshold = closed_ear_threshold
        self.partial_ear_threshold = partial_ear_threshold
        self._closure_start_time: Optional[float] = None
        self._current_closure_duration_ms: float = 0.0

    def process_landmarks(
        self, landmarks: Optional[List[Dict[str, float]]], timestamp_sec: Optional[float] = None
    ) -> Tuple[EyeStatusEnum, float, float]:
        """
        Analyzes landmarks and returns:
        (EyeStatusEnum, continuous_closure_duration_ms, mean_ear_score)
        """
        current_time = timestamp_sec if timestamp_sec is not None else time.time()

        if not landmarks or len(landmarks) < 400:
            # Face lost or insufficient landmarks
            self._closure_start_time = None
            self._current_closure_duration_ms = 0.0
            return EyeStatusEnum.UNKNOWN, 0.0, 0.0

        left_ear = calculate_ear(landmarks, LEFT_EYE_INDICES)
        right_ear = calculate_ear(landmarks, RIGHT_EYE_INDICES)
        mean_ear = (left_ear + right_ear) / 2.0

        if mean_ear < self.closed_ear_threshold:
            status = EyeStatusEnum.CLOSED
            if self._closure_start_time is None:
                self._closure_start_time = current_time
            self._current_closure_duration_ms = max(
                0.0, (current_time - self._closure_start_time) * 1000.0
            )
        elif mean_ear < self.partial_ear_threshold:
            status = EyeStatusEnum.PARTIAL
            if self._closure_start_time is None:
                self._closure_start_time = current_time
            self._current_closure_duration_ms = max(
                0.0, (current_time - self._closure_start_time) * 1000.0
            )
        else:
            status = EyeStatusEnum.OPEN
            self._closure_start_time = None
            self._current_closure_duration_ms = 0.0

        return status, round(self._current_closure_duration_ms, 1), round(mean_ear, 3)

    def reset(self):
        """Resets closure duration counters."""
        self._closure_start_time = None
        self._current_closure_duration_ms = 0.0
