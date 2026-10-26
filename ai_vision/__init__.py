"""
AI Vision Package.
"""

from ai_vision.camera_manager import CameraManager
from ai_vision.face_landmark_detector import FaceLandmarkDetector
from ai_vision.eye_closure_detector import EyeClosureDetector, calculate_ear
from ai_vision.yawn_detector import YawnDetector, calculate_mar
from ai_vision.head_pose_estimator import HeadPoseEstimator
from ai_vision.vision_service import VisionService

__all__ = [
    "CameraManager",
    "FaceLandmarkDetector",
    "EyeClosureDetector",
    "calculate_ear",
    "YawnDetector",
    "calculate_mar",
    "HeadPoseEstimator",
    "VisionService",
]
