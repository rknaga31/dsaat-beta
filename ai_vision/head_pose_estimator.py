"""
Head Pose Estimator.
Estimates 3D head orientation (Pitch, Yaw, Roll) and detects micro-sleep nodding motions.
"""

import math
from typing import List, Dict, Tuple, Optional
from ai_vision.face_landmark_detector import NOSE_TIP, CHIN


class HeadPoseEstimator:
    """Estimates head rotation angles and detects downward nodding motions."""

    def __init__(self, nod_pitch_threshold_deg: float = 20.0):
        self.nod_pitch_threshold_deg = nod_pitch_threshold_deg

    def estimate_pose(
        self, landmarks: Optional[List[Dict[str, float]]]
    ) -> Tuple[float, float, float, bool]:
        """
        Calculates approximate (pitch, yaw, roll, head_nod_detected).
        Positive pitch angles indicate downward head drop (nodding off).
        """
        if not landmarks or len(landmarks) < 400:
            return 0.0, 0.0, 0.0, False

        nose = landmarks[NOSE_TIP]
        chin = landmarks[CHIN]

        # Geometric relative approximation of pitch via vertical distance and z-depth
        dy = chin["y"] - nose["y"]
        dz = chin["z"] - nose["z"]

        # Approximate pitch angle in degrees
        pitch_rad = math.atan2(dy, max(abs(dz), 0.001))
        # Map to degrees relative to standard upright face (~60-70 deg baseline)
        pitch_deg = (pitch_rad * 180.0 / math.pi) - 60.0

        yaw_deg = 0.0  # Placeholder for lateral rotation
        roll_deg = 0.0

        nod_detected = pitch_deg > self.nod_pitch_threshold_deg

        return (
            round(pitch_deg, 1),
            round(yaw_deg, 1),
            round(roll_deg, 1),
            nod_detected,
        )
