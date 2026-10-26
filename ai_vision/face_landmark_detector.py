"""
Face Landmark Detector.
Extracts facial mesh landmarks using MediaPipe FaceMesh or compatible computer vision pipelines.
"""

import logging
from typing import Optional, Any, Dict, List

logger = logging.getLogger("face_landmark_detector")

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    mp = None
    MEDIAPIPE_AVAILABLE = False


# Canonical MediaPipe FaceMesh Landmark Indices for Driver Monitoring
LEFT_EYE_INDICES = [362, 385, 387, 263, 373, 380]
RIGHT_EYE_INDICES = [33, 160, 158, 133, 153, 144]
LIPS_INNER_TOP = 13
LIPS_INNER_BOTTOM = 14
LIPS_CORNER_LEFT = 78
LIPS_CORNER_RIGHT = 308
NOSE_TIP = 1
CHIN = 152


class FaceLandmarkDetector:
    """Detects primary driver face and extracts key topological facial points."""

    def __init__(self, min_detection_confidence: float = 0.5, min_tracking_confidence: float = 0.5):
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.face_mesh = None

        if MEDIAPIPE_AVAILABLE:
            try:
                self.mp_face_mesh = mp.solutions.face_mesh
                self.face_mesh = self.mp_face_mesh.FaceMesh(
                    max_num_faces=1,
                    refine_landmarks=True,
                    min_detection_confidence=min_detection_confidence,
                    min_tracking_confidence=min_tracking_confidence,
                )
                logger.info("MediaPipe FaceMesh detector initialized.")
            except Exception as exc:
                logger.error(f"Failed to initialize MediaPipe FaceMesh: {exc}")
        else:
            logger.warning(
                "MediaPipe is not installed. Face landmark detector requires mediapipe. "
                "Run 'pip install mediapipe'."
            )

    def detect_landmarks(self, frame: Any) -> Optional[List[Dict[str, float]]]:
        """
        Processes RGB/BGR frame and returns list of normalized landmark coordinates {x, y, z}.
        Returns None if no face is detected or library is unavailable.
        """
        if not MEDIAPIPE_AVAILABLE or not self.face_mesh or frame is None:
            return None

        try:
            # MediaPipe expects RGB format
            rgb_frame = frame[:, :, ::-1]  # Convert BGR to RGB if numpy frame
            results = self.face_mesh.process(rgb_frame)

            if not results.multi_face_landmarks:
                return None

            primary_landmarks = results.multi_face_landmarks[0].landmark
            return [{"x": lm.x, "y": lm.y, "z": lm.z} for lm in primary_landmarks]
        except Exception as exc:
            logger.error(f"Error during landmark inference: {exc}")
            return None

    def close(self):
        """Frees model resources."""
        if self.face_mesh:
            self.face_mesh.close()
            self.face_mesh = None
