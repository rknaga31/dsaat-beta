import React, { useState, useEffect, useRef } from 'react';
import ReactDOM from 'react-dom';
import { SensorDataStatus, GpsFreshness, GpsPermission } from '../types';
import {
  sendSensorReading,
  sendGpsCoordinates,
  fetchNetworkInfo,
  fetchSmartwatchVerification,
  updateEmergencyContact,
} from '../services/apiClient';

export function SensorCard({ sensorData, gpsData, escalationData, sessionActive }) {
  const [showHealthModal, setShowHealthModal] = useState(false);
  const [showBoultModal, setShowBoultModal] = useState(false);
  const [showGpsModal, setShowGpsModal] = useState(false);
  const [showContactModal, setShowContactModal] = useState(false);
  const [networkInfo, setNetworkInfo] = useState(null);
  const [boultAudit, setBoultAudit] = useState(null);
  const [copiedKey, setCopiedKey] = useState(null);

  // Contact editing state
  const [newPhone, setNewPhone] = useState(escalationData?.emergency_contact_phone || '+919876543210');
  const [newName, setNewName] = useState(escalationData?.emergency_contact_name || 'Family Contact');

  // Browser Geolocation tracking state
  const [isBrowserGpsActive, setIsBrowserGpsActive] = useState(false);
  const [gpsError, setGpsError] = useState(null);
  const watchIdRef = useRef(null);

  useEffect(() => {
    fetchNetworkInfo().then((info) => {
      if (info) setNetworkInfo(info);
    });
    fetchSmartwatchVerification().then((audit) => {
      if (audit) setBoultAudit(audit);
    });
  }, []);

  // Sync phone edit state when backend updates
  useEffect(() => {
    if (escalationData?.emergency_contact_phone) {
      setNewPhone(escalationData.emergency_contact_phone);
    }
    if (escalationData?.emergency_contact_name) {
      setNewName(escalationData.emergency_contact_name);
    }
  }, [escalationData]);

  // Stop GPS collection when journey monitoring stops
  useEffect(() => {
    if (!sessionActive && isBrowserGpsActive) {
      stopBrowserGps();
    }
  }, [sessionActive]);

  const hr = sensorData?.heart_rate_bpm;
  const status = sensorData?.data_status || SensorDataStatus.UNAVAILABLE;
  const source = sensorData?.source || 'none';
  const freshnessSec = sensorData?.data_freshness_seconds;
  const errorMsg = sensorData?.error_state;

  const lat = gpsData?.latitude;
  const lon = gpsData?.longitude;
  const gpsFreshness = gpsData?.freshness_status || (lat ? GpsFreshness.LIVE : GpsFreshness.UNAVAILABLE);

  const getStatusBadge = () => {
    switch (status) {
      case SensorDataStatus.CONNECTED_LIVE:
      case 'LIVE':
        return <span className="badge badge-normal">LIVE BLE</span>;
      case SensorDataStatus.CONNECTED_HISTORICAL:
        return <span className="badge badge-info">HISTORICAL SYNC</span>;
      case SensorDataStatus.SIMULATED_DEMO:
      case 'SIMULATED':
        return <span className="badge badge-warning">SIMULATED DEMO</span>;
      case SensorDataStatus.STALE_DATA:
      case 'STALE':
        return <span className="badge badge-warning">STALE (&gt;10s)</span>;
      default:
        return <span className="badge badge-muted">UNPAIRED BLE</span>;
    }
  };

  const getGpsBadge = () => {
    switch (gpsFreshness) {
      case GpsFreshness.LIVE:
        return <span className="badge badge-normal">LIVE GPS</span>;
      case GpsFreshness.STALE:
        return <span className="badge badge-warning">STALE FIX</span>;
      case GpsFreshness.SIMULATED:
        return <span className="badge badge-warning">MOCK GPS</span>;
      default:
        return <span className="badge badge-muted">UNAVAILABLE</span>;
    }
  };

  const handleInjectBpm = async (bpmValue, sourceName = 'google_health_simulator', scenarioStatus = null) => {
    let targetStatus = 'SIMULATED';
    if (bpmValue === null) targetStatus = 'UNAVAILABLE';
    if (scenarioStatus) targetStatus = scenarioStatus === SensorDataStatus.STALE_DATA ? 'STALE' : 'SIMULATED';

    await sendSensorReading({
      timestamp: new Date().toISOString(),
      heart_rate_bpm: bpmValue,
      source: sourceName,
      data_status: targetStatus,
      connection_status: bpmValue !== null,
      data_freshness_seconds: scenarioStatus === SensorDataStatus.STALE_DATA ? 25.0 : 0.0,
      device_battery_percent: bpmValue ? 88.0 : null,
      error_state: bpmValue ? null : 'Simulated device disconnection',
    });
  };

  const startBrowserGps = () => {
    if (!navigator.geolocation) {
      setGpsError('Geolocation is not supported by your browser.');
      return;
    }
    setGpsError(null);
    setIsBrowserGpsActive(true);

    const id = navigator.geolocation.watchPosition(
      (pos) => {
        const { latitude, longitude, speed, accuracy } = pos.coords;
        sendGpsCoordinates({
          timestamp: new Date().toISOString(),
          latitude: latitude,
          longitude: longitude,
          speed_kmh: speed !== null && speed !== undefined ? Math.max(0, speed * 3.6) : 0.0,
          accuracy_meters: accuracy || 5.0,
          source: 'android_browser_gps',
          permission_status: 'GRANTED',
          freshness_status: 'LIVE',
          is_valid: true,
          error_state: null,
        });
      },
      (err) => {
        let errMsg = 'Browser geolocation error';
        let perm = 'DENIED';
        if (err.code === 1) {
          errMsg = 'Location permission denied by user or insecure HTTP context.';
        } else if (err.code === 2) {
          errMsg = 'GPS position unavailable (GPS turned off or indoors).';
          perm = 'UNAVAILABLE';
        } else if (err.code === 3) {
          errMsg = 'Location request timed out.';
        }
        setGpsError(errMsg);
        sendGpsCoordinates({
          timestamp: new Date().toISOString(),
          latitude: null,
          longitude: null,
          source: 'android_browser_gps',
          permission_status: perm,
          freshness_status: 'UNAVAILABLE',
          is_valid: false,
          error_state: errMsg,
        });
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 5000 }
    );
    watchIdRef.current = id;
  };

  const stopBrowserGps = () => {
    if (watchIdRef.current !== null) {
      navigator.geolocation.clearWatch(watchIdRef.current);
      watchIdRef.current = null;
    }
    setIsBrowserGpsActive(false);
  };

  const handleSaveContact = async () => {
    await updateEmergencyContact(newPhone, newName);
    setShowContactModal(false);
  };

  const copyToClipboard = (text, key) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const fallbackGpsWebhook = networkInfo?.gps_webhook_url || 'http://<LAPTOP_IP>:8000/api/v1/sensors/gps';
  const fallbackHealthWebhook = networkInfo?.health_connect_webhook_url || 'http://<LAPTOP_IP>:8000/api/v1/sensors/health_connect';

  return (
    <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* SECTION 1: Biometrics & Smartwatch */}
      <div className="inner-panel" style={{ display: 'flex', flexDirection: 'column', gap: '0.9rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '1.1rem' }}>⌚</span>
            <div>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc' }}>
                Biometrics: Boult Smartwatch
              </h3>
              <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
                Source: <code style={{ color: '#38bdf8' }}>{source}</code>
                {freshnessSec !== null && freshnessSec !== undefined && (
                  <span> • Age: {freshnessSec < 60 ? `${freshnessSec.toFixed(0)}s` : `${(freshnessSec / 60).toFixed(0)}m`}</span>
                )}
              </div>
            </div>
          </div>
          {getStatusBadge()}
        </div>

        {/* Heart Rate Display & Actions */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{
              width: '54px',
              height: '54px',
              borderRadius: '50%',
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.35)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '1.6rem',
            }} className={hr ? 'heartbeat-active' : ''}>
              ❤️
            </div>

            <div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.4rem' }}>
                <span style={{
                  fontSize: '2.4rem',
                  fontWeight: 800,
                  color: hr ? '#f8fafc' : '#64748b',
                  lineHeight: 1,
                  fontFamily: 'var(--font-mono)',
                }}>
                  {hr !== null && hr !== undefined ? Math.round(hr) : '--'}
                </span>
                <span style={{ color: 'var(--text-dim)', fontSize: '0.85rem', fontWeight: 700 }}>BPM</span>
              </div>
              <div style={{ fontSize: '0.76rem', color: hr ? '#10b981' : '#94a3b8', marginTop: '0.15rem' }}>
                {status === SensorDataStatus.UNAVAILABLE
                  ? 'Hardware pending pairing (Safe Fallback: Camera Only)'
                  : status === SensorDataStatus.STALE_DATA
                  ? '⚠️ Telemetry stale (>10s old)'
                  : 'Physiological stream active'}
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '0.45rem', flexWrap: 'wrap' }}>
            <button
              onClick={() => setShowBoultModal(true)}
              className="btn btn-secondary"
              style={{ fontSize: '0.75rem', padding: '0.4rem 0.7rem' }}
            >
              🔍 Boult Audit
            </button>
            <button
              onClick={() => setShowHealthModal(true)}
              className="btn btn-secondary"
              style={{ fontSize: '0.75rem', padding: '0.4rem 0.7rem' }}
            >
              🔗 Health Connect
            </button>
          </div>
        </div>

        {/* Hardware Diagnostic Banner if Unavailable */}
        {errorMsg && status === SensorDataStatus.UNAVAILABLE && (
          <div style={{
            background: 'rgba(245, 158, 11, 0.08)',
            borderLeft: '3px solid #f59e0b',
            padding: '0.45rem 0.7rem',
            borderRadius: '6px',
            fontSize: '0.74rem',
            color: '#cbd5e1',
          }}>
            <strong>Diagnostic:</strong> {errorMsg}
          </div>
        )}

        {/* Zero-Hardware Simulation Strip - Integrated directly with biometrics */}
        <div style={{
          background: 'rgba(0, 0, 0, 0.25)',
          padding: '0.65rem 0.85rem',
          borderRadius: '8px',
          border: '1px solid rgba(255, 255, 255, 0.04)',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.45rem',
        }}>
          <div style={{ fontSize: '0.7rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            🧪 Biometric Simulator Toggles:
          </div>
          <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
            <button
              onClick={() => handleInjectBpm(74.0, 'simulated_normal', SensorDataStatus.SIMULATED_DEMO)}
              className="btn btn-chip"
              style={{ color: '#10b981' }}
            >
              💚 Normal (74)
            </button>
            <button
              onClick={() => handleInjectBpm(48.0, 'simulated_drowsy', SensorDataStatus.SIMULATED_DEMO)}
              className="btn btn-chip"
              style={{ color: '#f59e0b' }}
            >
              ⚠️ Drowsy (48)
            </button>
            <button
              onClick={() => handleInjectBpm(122.0, 'simulated_panic', SensorDataStatus.SIMULATED_DEMO)}
              className="btn btn-chip"
              style={{ color: '#ef4444' }}
            >
              🚨 Panic (122)
            </button>
            <button
              onClick={() => handleInjectBpm(72.0, 'simulated_stale', SensorDataStatus.STALE_DATA)}
              className="btn btn-chip"
              style={{ color: '#f59e0b' }}
            >
              ⏳ Stale (25s)
            </button>
            <button
              onClick={() => handleInjectBpm(null, 'none', SensorDataStatus.UNAVAILABLE)}
              className="btn btn-chip"
              style={{ color: '#64748b' }}
            >
              ❌ Disconnect
            </button>
          </div>
        </div>
      </div>

      {/* SECTION 2: Android Phone GPS Bridge */}
      <div className="inner-panel" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '1.1rem' }}>📍</span>
            <span style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc' }}>Android Phone GPS Bridge</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
            {getGpsBadge()}
            <button
              onClick={() => setShowGpsModal(true)}
              className="btn btn-secondary"
              style={{ fontSize: '0.72rem', padding: '0.25rem 0.55rem' }}
            >
              ⚙️ Setup
            </button>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div>
            <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase' }}>Position Coordinates</div>
            <div style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '0.85rem',
              color: lat && lon ? '#38bdf8' : '#64748b',
              marginTop: '0.15rem',
            }}>
              {lat && lon ? `${lat.toFixed(4)}° N, ${lon.toFixed(4)}° E` : 'Unavailable (Signal not acquired)'}
            </div>
            <div style={{ fontSize: '0.7rem', color: '#64748b', marginTop: '0.15rem' }}>
              Source: {gpsData?.source || 'none'} • Perm: {gpsData?.permission_status || 'NOT_REQUESTED'}
            </div>
          </div>

          <div>
            {!isBrowserGpsActive ? (
              <button
                onClick={startBrowserGps}
                className="btn btn-secondary"
                style={{ fontSize: '0.78rem', padding: '0.4rem 0.8rem' }}
              >
                📡 Acquire Browser GPS
              </button>
            ) : (
              <button
                onClick={stopBrowserGps}
                className="btn btn-danger"
                style={{ fontSize: '0.78rem', padding: '0.4rem 0.8rem' }}
              >
                ⏹️ Stop GPS
              </button>
            )}
          </div>
        </div>

        {gpsError && (
          <div style={{
            background: 'rgba(239, 68, 68, 0.1)',
            borderLeft: '3px solid #ef4444',
            padding: '0.45rem 0.7rem',
            borderRadius: '6px',
            fontSize: '0.74rem',
            color: '#fca5a5',
          }}>
            {gpsError}
          </div>
        )}
      </div>

      {/* SECTION 3: Autonomous Escalation & Family SOS Dispatcher */}
      <div className="inner-panel" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '1.1rem' }}>🛡️</span>
            <span style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc' }}>
              Family SOS Dispatcher
            </span>
          </div>
          <button
            onClick={() => setShowContactModal(true)}
            className="btn btn-secondary"
            style={{ fontSize: '0.72rem', padding: '0.25rem 0.55rem' }}
          >
            ✏️ Edit Contact
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.75rem' }}>
          <div>
            <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase' }}>Recipient Contact</div>
            <div style={{ fontSize: '0.88rem', fontWeight: 700, color: '#f8fafc', marginTop: '0.15rem' }}>
              {escalationData?.emergency_contact_phone || '+919876543210'}
            </div>
            <div style={{ fontSize: '0.72rem', color: '#64748b' }}>
              {escalationData?.emergency_contact_name || 'Family Emergency Contact'}
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase' }}>SMS Provider / Stage</div>
            <div style={{ fontSize: '0.88rem', fontWeight: 700, color: '#38bdf8', marginTop: '0.15rem' }}>
              MOCK SENDER (SAFE)
            </div>
            <div style={{ fontSize: '0.72rem', color: '#64748b' }}>
              Stage: {escalationData?.stage || 'MONITORING'}
            </div>
          </div>
        </div>

        {escalationData?.last_sms_sent_at && (
          <div style={{
            fontSize: '0.74rem',
            color: '#10b981',
            background: 'rgba(16, 185, 129, 0.08)',
            padding: '0.4rem 0.65rem',
            borderRadius: '6px',
            border: '1px solid rgba(16, 185, 129, 0.2)',
          }}>
            Last SOS Dispatch: <strong>{escalationData.sms_status}</strong> at{' '}
            {new Date(escalationData.last_sms_sent_at).toLocaleTimeString()}
          </div>
        )}
      </div>

      {/* PORTAL MODALS - Rendered at document.body level to avoid clipping by parent backdrop-filters */}

      {/* Modal 1: Boult Compatibility Audit */}
      {showBoultModal && ReactDOM.createPortal(
        <div className="modal-overlay" onClick={() => setShowBoultModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '1.25rem 1.5rem',
              borderBottom: '1px solid rgba(255,255,255,0.08)',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <span style={{ fontSize: '1.2rem' }}>🔍</span>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>
                  Boult Smartwatch Compatibility Audit
                </h3>
              </div>
              <button
                onClick={() => setShowBoultModal(false)}
                style={{ background: 'transparent', border: 'none', color: '#94a3b8', fontSize: '1.5rem', cursor: 'pointer', lineHeight: 1 }}
              >
                ×
              </button>
            </div>

            <div style={{
              padding: '1.5rem',
              overflowY: 'auto',
              fontSize: '0.85rem',
              color: '#cbd5e1',
              lineHeight: 1.6,
              display: 'flex',
              flexDirection: 'column',
              gap: '1rem',
            }}>
              <div style={{
                background: 'rgba(239, 68, 68, 0.1)',
                borderLeft: '3px solid #ef4444',
                padding: '0.85rem 1rem',
                borderRadius: '8px',
              }}>
                <strong style={{ color: '#fca5a5' }}>Architectural Reality Notice:</strong> Boult consumer watches (Drift, Striker, Crown, Ridge) pair with proprietary apps (Boult Fit / Da Fit) and do not publish an open vendor cloud API. Direct BLE requires Heart Rate Service <code>0x180D</code>.
              </div>

              <div>
                <strong style={{ color: '#f8fafc' }}>Device Verification Procedure (Run on Android Phone):</strong>
                <ol style={{ paddingLeft: '1.25rem', marginTop: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                  {boultAudit?.verification_procedure?.map((step, idx) => (
                    <li key={idx}>{step}</li>
                  )) || (
                    <>
                      <li>Install <strong>nRF Connect for Mobile</strong> from Google Play.</li>
                      <li>Disconnect watch from Boult Fit app temporarily to release BLE lock.</li>
                      <li>Scan and connect to the watch. Look for Service <code>0x180D (Heart Rate)</code>.</li>
                      <li>If 0x180D is absent, use the <strong>Google Health Connect</strong> or <strong>Health Sync</strong> bridge.</li>
                    </>
                  )}
                </ol>
              </div>

              <div>
                <strong style={{ color: '#f8fafc' }}>Supported Integration Paths:</strong>
                <ul style={{ paddingLeft: '1.25rem', marginTop: '0.4rem', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                  <li><strong>Path A (Health Connect Bridge)</strong>: Boult Fit → Health Sync app → Google Health Connect → Wi-Fi webhook (Supported).</li>
                  <li><strong>Path B (Direct BLE)</strong>: Pending hardware verification of standard 0x180D GATT service.</li>
                </ul>
              </div>
            </div>

            <div style={{
              display: 'flex',
              justifyContent: 'flex-end',
              padding: '1rem 1.5rem',
              borderTop: '1px solid rgba(255,255,255,0.08)',
              background: 'rgba(0,0,0,0.2)',
            }}>
              <button onClick={() => setShowBoultModal(false)} className="btn btn-primary">
                Done
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}

      {/* Modal 2: Health Connect Setup */}
      {showHealthModal && ReactDOM.createPortal(
        <div className="modal-overlay" onClick={() => setShowHealthModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '1.25rem 1.5rem',
              borderBottom: '1px solid rgba(255,255,255,0.08)',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <span style={{ fontSize: '1.2rem' }}>🔗</span>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>
                  Health Connect Mobile Webhook Bridge
                </h3>
              </div>
              <button
                onClick={() => setShowHealthModal(false)}
                style={{ background: 'transparent', border: 'none', color: '#94a3b8', fontSize: '1.5rem', cursor: 'pointer' }}
              >
                ×
              </button>
            </div>

            <div style={{
              padding: '1.5rem',
              overflowY: 'auto',
              fontSize: '0.85rem',
              color: '#cbd5e1',
              lineHeight: 1.6,
              display: 'flex',
              flexDirection: 'column',
              gap: '1rem',
            }}>
              <p>Push real-time heart rate from your Android phone directly to this laptop over Wi-Fi.</p>

              <div>
                <strong>Webhook Target URL:</strong>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  background: '#020617',
                  padding: '0.6rem 0.85rem',
                  borderRadius: '8px',
                  border: '1px solid rgba(255,255,255,0.1)',
                  marginTop: '0.35rem',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.8rem',
                  color: '#38bdf8',
                }}>
                  <span style={{ flex: 1, wordBreak: 'break-all' }}>{fallbackHealthWebhook}</span>
                  <button
                    onClick={() => copyToClipboard(fallbackHealthWebhook, 'health')}
                    className="btn btn-secondary"
                    style={{ padding: '0.25rem 0.6rem', fontSize: '0.75rem', marginLeft: '0.5rem' }}
                  >
                    {copiedKey === 'health' ? '✓ Copied' : 'Copy'}
                  </button>
                </div>
              </div>

              <div>
                <strong>JSON Payload Sample:</strong>
                <pre style={{
                  background: '#020617',
                  padding: '0.75rem',
                  borderRadius: '8px',
                  fontSize: '0.75rem',
                  color: '#94a3b8',
                  fontFamily: 'var(--font-mono)',
                  marginTop: '0.35rem',
                }}>
{`{
  "heart_rate_bpm": 74.0,
  "source": "google_health_connect",
  "device_battery_percent": 85
}`}
                </pre>
              </div>
            </div>

            <div style={{
              display: 'flex',
              justifyContent: 'flex-end',
              padding: '1rem 1.5rem',
              borderTop: '1px solid rgba(255,255,255,0.08)',
              background: 'rgba(0,0,0,0.2)',
            }}>
              <button onClick={() => setShowHealthModal(false)} className="btn btn-primary">
                Done
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}

      {/* Modal 3: Android GPS Setup */}
      {showGpsModal && ReactDOM.createPortal(
        <div className="modal-overlay" onClick={() => setShowGpsModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '1.25rem 1.5rem',
              borderBottom: '1px solid rgba(255,255,255,0.08)',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <span style={{ fontSize: '1.2rem' }}>📍</span>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>
                  Android GPS Setup & Automation
                </h3>
              </div>
              <button
                onClick={() => setShowGpsModal(false)}
                style={{ background: 'transparent', border: 'none', color: '#94a3b8', fontSize: '1.5rem', cursor: 'pointer' }}
              >
                ×
              </button>
            </div>

            <div style={{
              padding: '1.5rem',
              overflowY: 'auto',
              fontSize: '0.85rem',
              color: '#cbd5e1',
              lineHeight: 1.6,
              display: 'flex',
              flexDirection: 'column',
              gap: '1rem',
            }}>
              <div>
                <strong>Android GPS Webhook URL:</strong>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  background: '#020617',
                  padding: '0.6rem 0.85rem',
                  borderRadius: '8px',
                  border: '1px solid rgba(255,255,255,0.1)',
                  marginTop: '0.35rem',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.8rem',
                  color: '#38bdf8',
                }}>
                  <span style={{ flex: 1, wordBreak: 'break-all' }}>{fallbackGpsWebhook}</span>
                  <button
                    onClick={() => copyToClipboard(fallbackGpsWebhook, 'gps')}
                    className="btn btn-secondary"
                    style={{ padding: '0.25rem 0.6rem', fontSize: '0.75rem', marginLeft: '0.5rem' }}
                  >
                    {copiedKey === 'gps' ? '✓ Copied' : 'Copy'}
                  </button>
                </div>
              </div>

              <div>
                <strong>Automation Options:</strong>
                <ul style={{ paddingLeft: '1.25rem', marginTop: '0.35rem', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                  <li><strong>Option 1: GPS Logger for Android</strong> (F-Droid / Play Store). Configure "Logging details" → "Log to OpenGTS or custom URL" with POST.</li>
                  <li><strong>Option 2: MacroDroid / Tasker</strong>. Trigger: Location changed → Action: HTTP POST to the webhook above.</li>
                  <li><strong>Option 3: Browser GPS</strong>. Click "Acquire Browser GPS" button on this dashboard.</li>
                </ul>
              </div>
            </div>

            <div style={{
              display: 'flex',
              justifyContent: 'flex-end',
              padding: '1rem 1.5rem',
              borderTop: '1px solid rgba(255,255,255,0.08)',
              background: 'rgba(0,0,0,0.2)',
            }}>
              <button onClick={() => setShowGpsModal(false)} className="btn btn-primary">
                Done
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}

      {/* Modal 4: Edit Contact */}
      {showContactModal && ReactDOM.createPortal(
        <div className="modal-overlay" onClick={() => setShowContactModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '1.25rem 1.5rem',
              borderBottom: '1px solid rgba(255,255,255,0.08)',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <span style={{ fontSize: '1.2rem' }}>✏️</span>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>
                  Configure Emergency Contact
                </h3>
              </div>
              <button
                onClick={() => setShowContactModal(false)}
                style={{ background: 'transparent', border: 'none', color: '#94a3b8', fontSize: '1.5rem', cursor: 'pointer' }}
              >
                ×
              </button>
            </div>

            <div style={{
              padding: '1.5rem',
              fontSize: '0.85rem',
              color: '#cbd5e1',
              display: 'flex',
              flexDirection: 'column',
              gap: '1rem',
            }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', color: '#94a3b8', marginBottom: '0.35rem' }}>
                  Contact Name
                </label>
                <input
                  type="text"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  style={{
                    width: '100%',
                    background: '#020617',
                    border: '1px solid rgba(255,255,255,0.15)',
                    borderRadius: '8px',
                    padding: '0.6rem 0.85rem',
                    color: '#f8fafc',
                    fontSize: '0.88rem',
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', color: '#94a3b8', marginBottom: '0.35rem' }}>
                  Phone Number (with country code)
                </label>
                <input
                  type="text"
                  value={newPhone}
                  onChange={(e) => setNewPhone(e.target.value)}
                  placeholder="+919876543210"
                  style={{
                    width: '100%',
                    background: '#020617',
                    border: '1px solid rgba(255,255,255,0.15)',
                    borderRadius: '8px',
                    padding: '0.6rem 0.85rem',
                    color: '#f8fafc',
                    fontSize: '0.88rem',
                  }}
                />
              </div>
            </div>

            <div style={{
              display: 'flex',
              justifyContent: 'flex-end',
              gap: '0.6rem',
              padding: '1rem 1.5rem',
              borderTop: '1px solid rgba(255,255,255,0.08)',
              background: 'rgba(0,0,0,0.2)',
            }}>
              <button onClick={() => setShowContactModal(false)} className="btn btn-secondary">
                Cancel
              </button>
              <button onClick={handleSaveContact} className="btn btn-primary">
                Save Contact
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </div>
  );
}
