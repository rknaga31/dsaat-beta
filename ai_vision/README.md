# AI and Computer Vision Module (`ai_vision/`)

**Module Owner:** Member 2 — AI & Computer Vision Engineer

---

## 1. Module Responsibility

The `ai_vision/` module handles non-intrusive driver monitoring through facial landmark tracking.
Key responsibilities:
1. **Camera Acquisition**: Capturing video frames at controlled frame rates (15–30 FPS) using `CameraManager`.
2. **Facial Topology Tracking**: Generating 478 3D landmarks via MediaPipe FaceMesh in `FaceLandmarkDetector`.
3. **Ocular Analysis**: Calculating Eye Aspect Ratio (EAR) and tracking continuous eye closure durations (`eye_closure_detector.py`).
4. **Yawn Detection**: Computing Mouth Aspect Ratio (MAR) and differentiating short speech movements from sustained fatigue yawns (`yawn_detector.py`).
5. **Head Pose Estimation**: Estimating pitch angle and detecting micro-sleep nodding motions (`head_pose_estimator.py`).
6. **Telemetry Packaging**: Formatting outputs into standard `VisionEventSchema` packets and dispatching them to the backend service.

---

## 2. Directory Structure

```text
ai_vision/
├── README.md                   # This specification
├── requirements.txt            # Vision-specific dependencies (opencv, mediapipe, scipy)
├── camera_manager.py           # Webcam device capture and FPS throttling
├── face_landmark_detector.py   # MediaPipe FaceMesh integration & landmark indices
├── eye_closure_detector.py     # EAR calculation & closure duration counter
├── yawn_detector.py            # MAR calculation & sustained yawn detection
├── head_pose_estimator.py      # 3D head pitch calculation & nod detection
├── vision_service.py           # Master pipeline orchestrator & HTTP forwarder
└── tests/
    └── test_vision_service.py  # Unit tests with synthetic landmark fixtures
```

---

## 3. Data Contract (Emitted Payload)

Every processed frame emits a payload conforming to `shared/schemas/vision_event.schema.json`:

```json
{
  "timestamp": "2026-10-26T12:00:00.000Z",
  "face_detected": true,
  "eye_status": "CLOSED",
  "eye_closure_duration_ms": 1850.0,
  "yawn_detected": false,
  "head_nod_detected": false,
  "tracking_reliable": true,
  "ear_score": 0.18,
  "mar_score": 0.22
}
```

---

## 4. Setup & Running

Install vision dependencies:

```bash
pip install -r ai_vision/requirements.txt
```

Run unit tests (no physical webcam required):

```bash
pytest ai_vision/tests/ -v
```

To run the vision service independently and forward events to the backend:

```python
from ai_vision.vision_service import VisionService

service = VisionService(camera_index=0, target_fps=15)
if service.start():
    event = service.process_single_frame()
    print("Detected:", event)
    service.stop()
```
