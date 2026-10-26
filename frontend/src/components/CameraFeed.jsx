import React, { useRef, useState, useEffect, useCallback } from 'react';
import { EyeStatus } from '../types';
import { sendVisionEvent } from '../services/apiClient';
import { playWarningTone, playCriticalAlarm } from '../services/soundEffects';

// MediaPipe FaceMesh Canonical Landmark Indices
const LEFT_EYE = [362, 385, 387, 263, 373, 380];
const RIGHT_EYE = [33, 160, 158, 133, 153, 144];
const NOSE_TIP = 1;
const CHIN = 152;
const FOREHEAD = 10;
const LEFT_CHEEK = 234;
const RIGHT_CHEEK = 454;
const LIPS_TOP = 13;
const LIPS_BOTTOM = 14;
const LIPS_LEFT = 78;
const LIPS_RIGHT = 308;

function dist(p1, p2) {
  return Math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2);
}

function calcEAR(landmarks, indices) {
  const p1 = landmarks[indices[0]];
  const p2 = landmarks[indices[1]];
  const p3 = landmarks[indices[2]];
  const p4 = landmarks[indices[3]];
  const p5 = landmarks[indices[4]];
  const p6 = landmarks[indices[5]];
  const v = dist(p2, p6) + dist(p3, p5);
  const h = 2 * dist(p1, p4);
  return h === 0 ? 0 : v / h;
}

function calcMAR(landmarks) {
  const top = landmarks[LIPS_TOP];
  const bottom = landmarks[LIPS_BOTTOM];
  const left = landmarks[LIPS_LEFT];
  const right = landmarks[LIPS_RIGHT];
  const v = dist(top, bottom);
  const h = dist(left, right);
  return h === 0 ? 0 : v / h;
}

export function CameraFeed({ visionData, compact = false }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  const [isCameraActive, setIsCameraActive] = useState(false);
  const [cameraError, setCameraError] = useState(null);
  const [detectorStatus, setDetectorStatus] = useState('Standby');

  // Live real-time metric states
  const [liveFaceDetected, setLiveFaceDetected] = useState(false);
  const [liveEyeStatus, setLiveEyeStatus] = useState(EyeStatus.OPEN);
  const [liveClosureMs, setLiveClosureMs] = useState(0);
  const [liveYawnDetected, setLiveYawnDetected] = useState(false);
  const [liveHeadNod, setLiveHeadNod] = useState(false);
  const [liveEAR, setLiveEAR] = useState(0.32);
  const [liveMAR, setLiveMAR] = useState(0.12);

  const closureStartTimeRef = useRef(null);
  const lastDispatchTimeRef = useRef(0);
  const faceMeshRef = useRef(null);
  const animFrameIdRef = useRef(null);

  // Initialize MediaPipe FaceMesh
  useEffect(() => {
    let isMounted = true;
    async function loadFaceMesh() {
      try {
        const { FaceMesh } = await import('@mediapipe/face_mesh');
        const mesh = new FaceMesh({
          locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`,
        });
        mesh.setOptions({
          maxNumFaces: 1,
          refineLandmarks: true,
          minDetectionConfidence: 0.5,
          minTrackingConfidence: 0.5,
        });

        mesh.onResults((results) => {
          if (!isMounted) return;
          handleLandmarkResults(results);
        });

        faceMeshRef.current = mesh;
        setDetectorStatus('AI FaceMesh Loaded');
      } catch (err) {
        console.warn('MediaPipe FaceMesh CDN load error, fallback active:', err);
        setDetectorStatus('Visual Fallback Ready');
      }
    }
    loadFaceMesh();
    return () => {
      isMounted = false;
      if (faceMeshRef.current?.close) {
        faceMeshRef.current.close();
      }
    };
  }, []);

  // Process live landmarks
  const handleLandmarkResults = useCallback((results) => {
    const canvas = canvasRef.current;
    const video = videoRef.current;
    if (!canvas || !video) return;

    const ctx = canvas.getContext('2d');
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (!results.multiFaceLandmarks || results.multiFaceLandmarks.length === 0) {
      setLiveFaceDetected(false);
      closureStartTimeRef.current = null;
      setLiveClosureMs(0);
      setLiveEyeStatus(EyeStatus.UNKNOWN);
      return;
    }

    const landmarks = results.multiFaceLandmarks[0];
    setLiveFaceDetected(true);

    // 1. Calculate EAR for both eyes
    const leftEar = calcEAR(landmarks, LEFT_EYE);
    const rightEar = calcEAR(landmarks, RIGHT_EYE);
    const ear = (leftEar + rightEar) / 2;
    setLiveEAR(parseFloat(ear.toFixed(2)));

    // 2. Calculate MAR for mouth opening
    const mar = calcMAR(landmarks);
    setLiveMAR(parseFloat(mar.toFixed(2)));

    const now = performance.now();

    // 3. Eye Closure Analysis
    let currentClosure = 0;
    let eyeStat = EyeStatus.OPEN;
    if (ear < 0.21) {
      eyeStat = EyeStatus.CLOSED;
      if (!closureStartTimeRef.current) {
        closureStartTimeRef.current = now;
      }
      currentClosure = Math.round(now - closureStartTimeRef.current);
      setLiveClosureMs(currentClosure);

      // Warning after 1.5s, Critical after 2.5s
      if (currentClosure >= 2500) {
        playCriticalAlarm();
      } else if (currentClosure >= 1500) {
        playWarningTone();
      }
    } else {
      eyeStat = EyeStatus.OPEN;
      closureStartTimeRef.current = null;
      setLiveClosureMs(0);
    }
    setLiveEyeStatus(eyeStat);

    // 4. Yawn Analysis (MAR > 0.55)
    const isYawning = mar >= 0.55;
    setLiveYawnDetected(isYawning);
    if (isYawning) {
      playWarningTone();
    }

    // 5. Draw Facial HUD with green neon box & mesh matching reference image
    drawOverlayHUD(ctx, canvas, landmarks, ear, mar, isYawning, currentClosure);

    // 6. Rate-limited Dispatch to Backend API (every 350ms)
    const wallNow = Date.now();
    if (wallNow - lastDispatchTimeRef.current >= 350) {
      lastDispatchTimeRef.current = wallNow;
      sendVisionEvent({
        timestamp: new Date().toISOString(),
        face_detected: true,
        eye_status: eyeStat,
        eye_closure_duration_ms: currentClosure,
        yawn_detected: isYawning,
        head_nod_detected: false,
        tracking_reliable: true,
        ear_score: parseFloat(ear.toFixed(2)),
        mar_score: parseFloat(mar.toFixed(2)),
      });
    }
  }, []);

  // Draw HUD graphics onto canvas: Green Face Box & Mesh matching user image
  const drawOverlayHUD = (ctx, canvas, landmarks, ear, mar, isYawning, closureMs) => {
    ctx.save();
    // Mirror overlay horizontally to match mirrored video
    ctx.translate(canvas.width, 0);
    ctx.scale(-1, 1);

    const w = canvas.width;
    const h = canvas.height;

    // Calculate face bounding box from key landmarks
    const xs = landmarks.map((p) => p.x * w);
    const ys = landmarks.map((p) => p.y * h);
    const minX = Math.min(...xs) - 15;
    const maxX = Math.max(...xs) + 15;
    const minY = Math.min(...ys) - 25;
    const maxY = Math.max(...ys) + 20;
    const boxW = maxX - minX;
    const boxH = maxY - minY;

    // 1. Neon Green Face Bounding Box with Corner Reticles (as in reference image)
    const boxColor = closureMs >= 2500 ? '#ef4444' : isYawning ? '#f59e0b' : '#10b981';
    ctx.strokeStyle = boxColor;
    ctx.lineWidth = 2.5;
    ctx.shadowColor = boxColor;
    ctx.shadowBlur = 10;

    // Draw rounded rectangle or corner brackets
    const corner = Math.min(24, boxW * 0.2);
    ctx.beginPath();
    // Top-left corner
    ctx.moveTo(minX, minY + corner);
    ctx.lineTo(minX, minY);
    ctx.lineTo(minX + corner, minY);
    // Top-right corner
    ctx.moveTo(maxX - corner, minY);
    ctx.lineTo(maxX, minY);
    ctx.lineTo(maxX, minY + corner);
    // Bottom-right corner
    ctx.moveTo(maxX, maxY - corner);
    ctx.lineTo(maxX, maxY);
    ctx.lineTo(maxX - corner, maxY);
    // Bottom-left corner
    ctx.moveTo(minX + corner, maxY);
    ctx.lineTo(minX, maxY);
    ctx.lineTo(minX, maxY - corner);
    ctx.stroke();

    // 2. Facial Feature Mesh Dots (Eyes, Nose, Mouth) in bright neon green
    ctx.shadowBlur = 0;
    ctx.fillStyle = '#10b981';
    [...LEFT_EYE, ...RIGHT_EYE, NOSE_TIP, CHIN, FOREHEAD, LEFT_CHEEK, RIGHT_CHEEK, LIPS_TOP, LIPS_BOTTOM].forEach((idx) => {
      const pt = landmarks[idx];
      if (!pt) return;
      ctx.beginPath();
      ctx.arc(pt.x * w, pt.y * h, 2.5, 0, 2 * Math.PI);
      ctx.fill();
    });

    // 3. Connect nose & mouth bridge
    ctx.strokeStyle = 'rgba(16, 185, 129, 0.45)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(landmarks[NOSE_TIP].x * w, landmarks[NOSE_TIP].y * h);
    ctx.lineTo(landmarks[LIPS_TOP].x * w, landmarks[LIPS_TOP].y * h);
    ctx.lineTo(landmarks[CHIN].x * w, landmarks[CHIN].y * h);
    ctx.stroke();

    ctx.restore();
  };

  // Start live webcam capture
  const handleStartCamera = async () => {
    setCameraError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' },
        audio: false,
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => {
          videoRef.current.play();
          setIsCameraActive(true);
          startVisionProcessingLoop();
        };
      }
    } catch (err) {
      console.error('Camera access failed:', err);
      setCameraError('Camera access denied or device unavailable. Please allow webcam permissions in your browser.');
    }
  };

  // Stop webcam capture
  const handleStopCamera = () => {
    if (videoRef.current?.srcObject) {
      videoRef.current.srcObject.getTracks().forEach((track) => track.stop());
      videoRef.current.srcObject = null;
    }
    if (animFrameIdRef.current) {
      cancelAnimationFrame(animFrameIdRef.current);
    }
    setIsCameraActive(false);
    setLiveFaceDetected(false);
    setLiveClosureMs(0);
    setLiveYawnDetected(false);
  };

  // Continuous frame processing loop
  const startVisionProcessingLoop = () => {
    const processFrame = async () => {
      if (videoRef.current && videoRef.current.readyState >= 2 && faceMeshRef.current) {
        try {
          await faceMeshRef.current.send({ image: videoRef.current });
        } catch (e) {
          // Frame drop safe
        }
      }
      animFrameIdRef.current = requestAnimationFrame(processFrame);
    };
    animFrameIdRef.current = requestAnimationFrame(processFrame);
  };

  // Simulations
  const handleSimulateYawn = async () => {
    setLiveYawnDetected(true);
    setLiveMAR(0.68);
    playWarningTone();
    await sendVisionEvent({
      timestamp: new Date().toISOString(),
      face_detected: true,
      eye_status: EyeStatus.OPEN,
      eye_closure_duration_ms: 0,
      yawn_detected: true,
      head_nod_detected: false,
      tracking_reliable: true,
      ear_score: 0.32,
      mar_score: 0.68,
    });
    setTimeout(() => {
      setLiveYawnDetected(false);
      setLiveMAR(0.12);
    }, 3000);
  };

  const handleSimulateCriticalEyeClosure = async () => {
    setLiveEyeStatus(EyeStatus.CLOSED);
    setLiveClosureMs(2800);
    setLiveEAR(0.12);
    setLiveHeadNod(true);
    playCriticalAlarm();
    await sendVisionEvent({
      timestamp: new Date().toISOString(),
      face_detected: true,
      eye_status: EyeStatus.CLOSED,
      eye_closure_duration_ms: 2800,
      yawn_detected: false,
      head_nod_detected: true,
      tracking_reliable: true,
      ear_score: 0.12,
      mar_score: 0.15,
    });
    setTimeout(() => {
      setLiveEyeStatus(EyeStatus.OPEN);
      setLiveClosureMs(0);
      setLiveEAR(0.32);
      setLiveHeadNod(false);
    }, 4500);
  };

  const displayFaceDetected = isCameraActive ? liveFaceDetected : visionData?.face_detected;
  const displayClosureMs = isCameraActive ? liveClosureMs : (visionData?.eye_closure_seconds ? visionData.eye_closure_seconds * 1000 : 0);
  const displayYawn = isCameraActive ? liveYawnDetected : visionData?.is_yawning;

  return (
    <div className="glass-panel" style={{
      display: 'flex',
      flexDirection: 'column',
      gap: '0.85rem',
      padding: '1.25rem',
      borderRadius: '18px',
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Viewfinder Frame Container with Live Badge */}
      <div style={{
        position: 'relative',
        width: '100%',
        height: '240px',
        background: '#040812',
        borderRadius: '14px',
        overflow: 'hidden',
        border: `2px solid ${displayYawn ? '#f59e0b' : (displayClosureMs >= 2500 ? '#ef4444' : 'rgba(16, 185, 129, 0.4)')}`,
        boxShadow: displayClosureMs >= 2500 ? '0 0 25px rgba(239, 68, 68, 0.4)' : (displayYawn ? '0 0 20px rgba(245, 158, 11, 0.3)' : '0 0 15px rgba(16, 185, 129, 0.15)'),
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}>
        {/* Real Live HTML5 Video Element */}
        <video
          ref={videoRef}
          playsInline
          muted
          style={{
            position: 'absolute',
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: 'scaleX(-1)',
            display: isCameraActive ? 'block' : 'none',
          }}
        />

        {/* Real-time Facial Landmark Overlay Canvas */}
        <canvas
          ref={canvasRef}
          style={{
            position: 'absolute',
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            pointerEvents: 'none',
            display: isCameraActive ? 'block' : 'none',
          }}
        />

        {/* Standby Placeholder when camera is off */}
        {!isCameraActive && (
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '0.65rem',
            textAlign: 'center',
            padding: '1rem',
          }}>
            <div style={{
              width: '58px',
              height: '58px',
              borderRadius: '50%',
              background: 'rgba(16, 185, 129, 0.1)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '1.75rem',
            }}>
              🚘
            </div>
            <div>
              <div style={{ fontWeight: 700, color: '#f8fafc', fontSize: '0.92rem' }}>
                Driver AI Live Feed
              </div>
              <div style={{ fontSize: '0.76rem', color: '#94a3b8', marginTop: '0.15rem' }}>
                FaceMesh facial landmarks & ocular tracker
              </div>
            </div>
          </div>
        )}

        {/* Top-Right "Live" Green Pill Badge matching reference image */}
        <div style={{
          position: 'absolute',
          top: '12px',
          right: '12px',
          background: isCameraActive || displayFaceDetected ? '#10b981' : 'rgba(16, 185, 129, 0.25)',
          color: '#ffffff',
          fontWeight: 800,
          fontSize: '0.75rem',
          padding: '0.22rem 0.65rem',
          borderRadius: '9999px',
          boxShadow: '0 2px 10px rgba(16, 185, 129, 0.4)',
          letterSpacing: '0.04em',
          display: 'flex',
          alignItems: 'center',
          gap: '0.35rem',
        }}>
          <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#fff' }} />
          <span>Live</span>
        </div>

        {/* Active Yawn / Sleep Alerts */}
        {displayYawn && (
          <div style={{
            position: 'absolute',
            bottom: '12px',
            background: 'rgba(245, 158, 11, 0.95)',
            color: '#000',
            fontWeight: 800,
            fontSize: '0.78rem',
            padding: '0.25rem 0.75rem',
            borderRadius: '9999px',
          }}>
            🥱 YAWN DETECTED
          </div>
        )}

        {displayClosureMs > 0 && (
          <div style={{
            position: 'absolute',
            bottom: '12px',
            background: displayClosureMs >= 2500 ? 'rgba(239, 68, 68, 0.95)' : 'rgba(245, 158, 11, 0.95)',
            color: '#fff',
            fontWeight: 800,
            fontSize: '0.78rem',
            padding: '0.25rem 0.75rem',
            borderRadius: '9999px',
          }}>
            Eyes Closed: {(displayClosureMs / 1000).toFixed(1)}s
          </div>
        )}
      </div>

      {/* Camera Action Buttons */}
      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
        {!isCameraActive ? (
          <button onClick={handleStartCamera} className="btn btn-primary" style={{ flex: 1, fontSize: '0.8rem', padding: '0.45rem 0.8rem' }}>
            🎥 Start Camera
          </button>
        ) : (
          <button onClick={handleStopCamera} className="btn btn-danger" style={{ flex: 1, fontSize: '0.8rem', padding: '0.45rem 0.8rem' }}>
            ⏹️ Stop Camera
          </button>
        )}

        <button onClick={handleSimulateYawn} className="btn btn-secondary" style={{ fontSize: '0.78rem', padding: '0.45rem 0.7rem' }}>
          🥱 Test Yawn
        </button>

        <button onClick={handleSimulateCriticalEyeClosure} className="btn btn-secondary" style={{ fontSize: '0.78rem', padding: '0.45rem 0.7rem' }}>
          😴 Test Sleep
        </button>
      </div>

      {cameraError && (
        <div style={{ fontSize: '0.75rem', color: '#fca5a5', background: 'rgba(239,68,68,0.1)', padding: '0.4rem', borderRadius: '6px' }}>
          {cameraError}
        </div>
      )}
    </div>
  );
}
