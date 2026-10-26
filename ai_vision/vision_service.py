"""
Vision Service Pipeline.
Coordinates camera acquisition, facial landmark detection, ocular tracking,
yawn analysis, and head pose estimation into standardized VisionEventSchema payloads.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import requests

from backend.schemas.vision_schema import VisionEventSchema
from shared.constants import EyeStatusEnum
from ai_vision.camera_manager import CameraManager
from ai_vision.face_landmark_detector import FaceLandmarkDetector
from ai_vision.eye_closure_detector import EyeClosureDetector
from ai_vision.yawn_detector import YawnDetector
from ai_vision.head_pose_estimator import HeadPoseEstimator

logger = logging.getLogger("vision_service")


class VisionService:
    """Master pipeline orchestrator for AI computer vision inference."""

    def __init__(
        self,
        camera_index: int = 0,
        target_fps: int = 15,
        backend_api_url: str = "http://127.0.0.1:8000/api/v1/monitoring/vision",
    ):
        self.camera_manager = CameraManager(camera_index=camera_index, target_fps=target_fps)
        self.landmark_detector = FaceLandmarkDetector()
        self.eye_detector = EyeClosureDetector()
        self.yawn_detector = YawnDetector()
        self.head_pose_estimator = HeadPoseEstimator()
        self.backend_api_url = backend_api_url
        self.is_running = False

    def start(self) -> bool:
        """Starts video capture hardware and begins tracking."""
        success = self.camera_manager.start_camera()
        if success:
            self.is_running = True
        return success

    def stop(self):
        """Stops hardware capture and frees landmark models."""
        self.is_running = False
        self.camera_manager.stop_camera()
        self.landmark_detector.close()

    def process_single_frame(self) -> VisionEventSchema:
        """
        Reads one frame from camera, computes all vision metrics, and produces
        a validated VisionEventSchema conforming to shared contracts.
        """
        now_iso = datetime.now(timezone.utc).isoformat()

        success, frame = self.camera_manager.read_frame()

        if not success or frame is None:
            # Camera unavailable or frame dropped
            return VisionEventSchema(
                timestamp=now_iso,
                face_detected=False,
                eye_status=EyeStatusEnum.UNKNOWN,
                eye_closure_duration_ms=0.0,
                yawn_detected=False,
                head_nod_detected=False,
                tracking_reliable=False,
            )

        landmarks = self.landmark_detector.detect_landmarks(frame)

        if not landmarks:
            # Face not detected in frame
            return VisionEventSchema(
                timestamp=now_iso,
                face_detected=False,
                eye_status=EyeStatusEnum.UNKNOWN,
                eye_closure_duration_ms=0.0,
                yawn_detected=False,
                head_nod_detected=False,
                tracking_reliable=False,
            )

        # Compute ocular metrics
        eye_status, closure_duration_ms, ear_score = self.eye_detector.process_landmarks(landmarks)

        # Compute yawn metrics
        yawn_detected, mar_score = self.yawn_detector.process_landmarks(landmarks)

        # Compute head pose metrics
        pitch, yaw, roll, nod_detected = self.head_pose_estimator.estimate_pose(landmarks)

        return VisionEventSchema(
            timestamp=now_iso,
            face_detected=True,
            eye_status=eye_status,
            eye_closure_duration_ms=closure_duration_ms,
            yawn_detected=yawn_detected,
            head_nod_detected=nod_detected,
            tracking_reliable=True,
            ear_score=ear_score,
            mar_score=mar_score,
        )

    def dispatch_event_to_backend(self, event: VisionEventSchema) -> Optional[Dict[str, Any]]:
        """HTTP POST forwarder sending real-time vision telemetry to the backend service."""
        try:
            response = requests.post(
                self.backend_api_url,
                json=event.model_dump(),
                timeout=1.0,
            )
            if response.status_code == 200:
                return response.json()
            logger.warning(f"Backend rejected vision event: HTTP {response.status_code}")
        except Exception as exc:
            logger.debug(f"Could not connect to backend API: {exc}")
        return None
