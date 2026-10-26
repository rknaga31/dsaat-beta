"""
Unit tests for AI Vision algorithms (EAR, MAR, and Nod Detection).
Uses synthetic mock landmarks to verify pure algorithmic correctness without hardware dependencies.
"""

import pytest
from ai_vision.eye_closure_detector import EyeClosureDetector, calculate_ear
from ai_vision.yawn_detector import YawnDetector, calculate_mar
from ai_vision.head_pose_estimator import HeadPoseEstimator
from ai_vision.face_landmark_detector import (
    LEFT_EYE_INDICES,
    LIPS_INNER_TOP,
    LIPS_INNER_BOTTOM,
    LIPS_CORNER_LEFT,
    LIPS_CORNER_RIGHT,
    NOSE_TIP,
    CHIN,
)
from shared.constants import EyeStatusEnum


@pytest.fixture
def base_landmarks():
    """Generates 478 mock landmarks with neutral default coordinates."""
    return [{"x": 0.5, "y": 0.5, "z": 0.0} for _ in range(478)]


def test_ear_calculation_open_eye(base_landmarks):
    """Synthetic open eye with wide vertical spacing should yield high EAR (>0.30)."""
    # Open eye: horizontal distance 0.1, vertical distances 0.04
    p1_idx, p2_idx, p3_idx, p4_idx, p5_idx, p6_idx = LEFT_EYE_INDICES
    base_landmarks[p1_idx] = {"x": 0.40, "y": 0.50, "z": 0.0}
    base_landmarks[p4_idx] = {"x": 0.50, "y": 0.50, "z": 0.0}  # width = 0.10

    base_landmarks[p2_idx] = {"x": 0.43, "y": 0.48, "z": 0.0}
    base_landmarks[p6_idx] = {"x": 0.43, "y": 0.52, "z": 0.0}  # height1 = 0.04

    base_landmarks[p3_idx] = {"x": 0.47, "y": 0.48, "z": 0.0}
    base_landmarks[p5_idx] = {"x": 0.47, "y": 0.52, "z": 0.0}  # height2 = 0.04

    ear = calculate_ear(base_landmarks, LEFT_EYE_INDICES)
    # EAR = (0.04 + 0.04) / (2 * 0.10) = 0.40
    assert pytest.approx(ear, 0.01) == 0.40


def test_eye_closure_detector_transitions(base_landmarks):
    """Detector should track continuous closure time between frames."""
    detector = EyeClosureDetector(closed_ear_threshold=0.21)

    # Mock closed eye: tiny vertical spacing
    for idx in LEFT_EYE_INDICES:
        base_landmarks[idx] = {"x": 0.45, "y": 0.50, "z": 0.0}

    # Frame 1: at t=10.0s
    status1, dur1, _ = detector.process_landmarks(base_landmarks, timestamp_sec=10.0)
    assert status1 == EyeStatusEnum.CLOSED
    assert dur1 == 0.0

    # Frame 2: at t=11.5s (1500 ms closed)
    status2, dur2, _ = detector.process_landmarks(base_landmarks, timestamp_sec=11.5)
    assert status2 == EyeStatusEnum.CLOSED
    assert pytest.approx(dur2, 10.0) == 1500.0


def test_yawn_detector(base_landmarks):
    """Sustained high MAR should trigger yawn detection."""
    detector = YawnDetector(mar_threshold=0.55, min_yawn_duration_ms=1500.0)

    # Set wide open mouth: vertical = 0.08, horizontal = 0.10 => MAR = 0.8
    base_landmarks[LIPS_CORNER_LEFT] = {"x": 0.45, "y": 0.70, "z": 0.0}
    base_landmarks[LIPS_CORNER_RIGHT] = {"x": 0.55, "y": 0.70, "z": 0.0}
    base_landmarks[LIPS_INNER_TOP] = {"x": 0.50, "y": 0.66, "z": 0.0}
    base_landmarks[LIPS_INNER_BOTTOM] = {"x": 0.50, "y": 0.74, "z": 0.0}

    # At t=0s: not yet triggered
    yawn1, mar1 = detector.process_landmarks(base_landmarks, timestamp_sec=0.0)
    assert yawn1 is False
    assert mar1 > 0.55

    # At t=2.0s: sustained > 1500ms => triggers True
    yawn2, mar2 = detector.process_landmarks(base_landmarks, timestamp_sec=2.0)
    assert yawn2 is True


def test_head_pose_nod_detection(base_landmarks):
    """Severe downward pitch should trigger nod detected flag."""
    estimator = HeadPoseEstimator(nod_pitch_threshold_deg=20.0)

    base_landmarks[NOSE_TIP] = {"x": 0.5, "y": 0.4, "z": 0.0}
    # Chin dropped significantly down with little depth
    base_landmarks[CHIN] = {"x": 0.5, "y": 0.9, "z": 0.05}

    pitch, yaw, roll, nod_detected = estimator.estimate_pose(base_landmarks)
    assert pitch > 20.0
    assert nod_detected is True
