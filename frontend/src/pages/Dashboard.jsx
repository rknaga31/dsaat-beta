import React, { useState, useEffect, useRef } from 'react';
import ReactDOM from 'react-dom';
import { useMonitoring } from '../hooks/useMonitoring';
import { Sidebar } from '../components/Sidebar';
import { CameraFeed } from '../components/CameraFeed';
import { RiskGaugeCard } from '../components/RiskGaugeCard';
import { BiometricMetricsCard } from '../components/BiometricMetricsCard';
import { TripTimelineChart } from '../components/TripTimelineChart';
import { AlertBanner } from '../components/AlertBanner';
import { EventHistory } from '../components/EventHistory';
import { SensorCard } from '../components/SensorCard';
import { RiskCard } from '../components/RiskCard';
import {
  testBuzzer,
  fetchNetworkInfo,
  fetchSmartwatchVerification,
  updateEmergencyContact,
  sendSensorReading,
  sendGpsCoordinates,
} from '../services/apiClient';
import { SensorDataStatus } from '../types';

export function Dashboard() {
  const {
    statusData,
    alerts,
    loading,
    isBackendOffline,
    startSession,
    endSession,
    triggerSos,
    acknowledge,
  } = useMonitoring(1500);

  const [activeTab, setActiveTab] = useState('dashboard');
  const [currentTime, setCurrentTime] = useState('');
  const [networkInfo, setNetworkInfo] = useState(null);
  const [boultAudit, setBoultAudit] = useState(null);

  // Modals state
  const [showNetworkModal, setShowNetworkModal] = useState(false);
  const [showBoultModal, setShowBoultModal] = useState(false);
  const [showHealthModal, setShowHealthModal] = useState(false);
  const [showGpsModal, setShowGpsModal] = useState(false);
  const [showContactModal, setShowContactModal] = useState(false);
  const [copiedKey, setCopiedKey] = useState(null);
  const [buzzerTesting, setBuzzerTesting] = useState(false);

  // Contact editing state
  const [newPhone, setNewPhone] = useState(statusData?.escalation?.emergency_contact_phone || '+919876543210');
  const [newName, setNewName] = useState(statusData?.escalation?.emergency_contact_name || 'Family Contact');

  // Live real-time clock matching reference image format: e.g. "Oct 25, 2026   10:24 AM"
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const optionsDate = { month: 'short', day: 'numeric', year: 'numeric' };
      const optionsTime = { hour: 'numeric', minute: '2-digit', hour12: true };
      const dateStr = now.toLocaleDateString('en-US', optionsDate);
      const timeStr = now.toLocaleTimeString('en-US', optionsTime);
      setCurrentTime(`${dateStr}   ${timeStr}`);
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    fetchNetworkInfo().then((info) => {
      if (info) setNetworkInfo(info);
    });
    fetchSmartwatchVerification().then((audit) => {
      if (audit) setBoultAudit(audit);
    });
  }, []);

  const isActive = statusData?.is_active ?? false;
  const tripDurationSec = statusData?.trip_duration_seconds ?? 0;

  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleTestBuzzer = async () => {
    setBuzzerTesting(true);
    await testBuzzer('WARNING');
    setTimeout(() => setBuzzerTesting(false), 800);
  };

  const [activeBaselineBpm, setActiveBaselineBpm] = useState(74.0);
  const [isAutoFluctuating, setIsAutoFluctuating] = useState(true);
  const fluctuationTickRef = useRef(0);

  // Periodically send fluctuating heart rate to backend API when active
  useEffect(() => {
    if (!isAutoFluctuating || activeBaselineBpm === null) return;

    const interval = setInterval(() => {
      fluctuationTickRef.current += 1;
      const t = fluctuationTickRef.current;
      // Gentle sinus rhythm jitter ±1 to ±3 BPM
      const jitter = Math.round(Math.sin(t * 0.5) * 2 + Math.cos(t * 0.9) * 1);
      const fluctuatingBpm = Math.max(35, Math.min(220, activeBaselineBpm + jitter));

      sendSensorReading({
        timestamp: new Date().toISOString(),
        heart_rate_bpm: fluctuatingBpm,
        source: 'google_health_simulator',
        data_status: 'SIMULATED',
        connection_status: true,
        data_freshness_seconds: 0.0,
        device_battery_percent: 88.0,
        error_state: null,
      });
    }, 2500); // sync with backend every 2.5s

    return () => clearInterval(interval);
  }, [activeBaselineBpm, isAutoFluctuating]);

  const handleInjectBpm = async (bpmValue, sourceName = 'google_health_simulator', scenarioStatus = null) => {
    if (bpmValue === null || scenarioStatus === SensorDataStatus.UNAVAILABLE) {
      setIsAutoFluctuating(false);
      setActiveBaselineBpm(null);
      await sendSensorReading({
        timestamp: new Date().toISOString(),
        heart_rate_bpm: null,
        source: 'none',
        data_status: 'UNAVAILABLE',
        connection_status: false,
        data_freshness_seconds: null,
        device_battery_percent: null,
        error_state: 'Simulated device disconnection',
      });
      return;
    }

    if (scenarioStatus === SensorDataStatus.STALE_DATA) {
      setIsAutoFluctuating(false);
      setActiveBaselineBpm(bpmValue);
      await sendSensorReading({
        timestamp: new Date().toISOString(),
        heart_rate_bpm: bpmValue,
        source: sourceName,
        data_status: 'STALE',
        connection_status: true,
        data_freshness_seconds: 25.0,
        device_battery_percent: 85.0,
        error_state: 'Simulated biometric reading is stale (>10s old).',
      });
      return;
    }

    // Set new baseline and enable continuous fluctuation stream
    setActiveBaselineBpm(bpmValue);
    setIsAutoFluctuating(true);
    await sendSensorReading({
      timestamp: new Date().toISOString(),
      heart_rate_bpm: bpmValue,
      source: sourceName,
      data_status: 'SIMULATED',
      connection_status: true,
      data_freshness_seconds: 0.0,
      device_battery_percent: 88.0,
      error_state: null,
    });
  };

  const copyToClipboard = (text, key) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const handleSaveContact = async () => {
    await updateEmergencyContact(newPhone, newName);
    setShowContactModal(false);
  };

  const fallbackGpsWebhook = networkInfo?.gps_webhook_url || 'http://<LAPTOP_IP>:8000/api/v1/sensors/gps';
  const fallbackHealthWebhook = networkInfo?.health_connect_webhook_url || 'http://<LAPTOP_IP>:8000/api/v1/sensors/health_connect';

  return (
    <div style={{
      maxWidth: '1360px',
      margin: '0 auto',
      padding: '1.25rem 1.5rem',
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      gap: '1.15rem',
    }}>
      {/* 1. TOP HEADER (Matching Reference Image) */}
      <header style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingBottom: '0.75rem',
        borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
        flexWrap: 'wrap',
        gap: '1rem',
      }}>
        {/* Left: Dashboard Icon + Title */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{
            width: '36px',
            height: '36px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #1e3a8a 0%, #0284c7 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.25rem',
            boxShadow: '0 0 15px rgba(2, 132, 199, 0.4)',
            border: '1px solid rgba(56, 189, 248, 0.4)',
          }}>
            🚘
          </div>
          <h1 style={{
            fontSize: '1.28rem',
            fontWeight: 800,
            color: '#f8fafc',
            letterSpacing: '-0.02em',
          }}>
            Driver Monitoring System
          </h1>
        </div>

        {/* Right: Real-time Date & Time + Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.15rem', flexWrap: 'wrap' }}>
          {isBackendOffline && (
            <span className="badge badge-danger">
              Backend Offline (127.0.0.1:8000)
            </span>
          )}

          {/* Real-time Clock display matching reference image */}
          <div style={{
            fontSize: '0.92rem',
            fontWeight: 600,
            color: '#94a3b8',
            letterSpacing: '0.02em',
          }}>
            {currentTime}
          </div>

          {/* Trip Status Pill */}
          <div style={{
            background: 'rgba(15, 23, 42, 0.85)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            padding: '0.35rem 0.75rem',
            borderRadius: '8px',
            fontSize: '0.8rem',
            fontFamily: 'var(--font-mono)',
            color: '#38bdf8',
            display: 'flex',
            alignItems: 'center',
            gap: '0.45rem',
          }}>
            <span className={`live-pulse-dot ${isActive ? 'dot-green' : 'dot-red'}`} />
            <span>{isActive ? 'TRIP' : 'STANDBY'}: {formatDuration(tripDurationSec)}</span>
          </div>

          {isActive ? (
            <button onClick={endSession} className="btn btn-secondary" style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}>
              End Trip
            </button>
          ) : (
            <button onClick={() => startSession('driver_semester')} className="btn btn-primary" style={{ padding: '0.4rem 0.85rem', fontSize: '0.8rem' }}>
              Start Trip
            </button>
          )}

          <button onClick={handleTestBuzzer} className="btn btn-secondary" style={{ padding: '0.4rem 0.75rem', fontSize: '0.8rem', color: buzzerTesting ? '#f59e0b' : '#cbd5e1' }}>
            🔔 {buzzerTesting ? 'Beeping...' : 'Test Buzzer'}
          </button>

          <button onClick={triggerSos} className="btn btn-danger" style={{ padding: '0.4rem 0.85rem', fontSize: '0.8rem' }}>
            🚨 SOS
          </button>
        </div>
      </header>

      {/* Safety Escalation Banner if Warning or Drowsiness is Active */}
      <AlertBanner
        riskState={statusData?.risk_state}
        activeAlert={statusData?.active_alert}
        escalation={statusData?.escalation}
        onAcknowledge={acknowledge}
      />

      {/* 2. BODY LAYOUT: LEFT SIDEBAR + RIGHT MAIN COCKPIT */}
      <div style={{
        display: 'flex',
        gap: '1.4rem',
        alignItems: 'flex-start',
        flexWrap: 'wrap',
      }}>
        {/* Left Navigation Sidebar */}
        <Sidebar activeTab={activeTab} onSelectTab={setActiveTab} />

        {/* Right Main Content Area */}
        <main style={{ flex: 1, minWidth: '320px', display: 'flex', flexDirection: 'column', gap: '1.35rem' }}>
          {/* TAB 1: DASHBOARD (EXACT COCKPIT LAYOUT FROM REFERENCE IMAGE) */}
          {activeTab === 'dashboard' && (
            <>
              {/* TOP TIER: 3 Columns (Live Video + Radial Gauge + Heart Rate/HRV Stack) */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'minmax(280px, 1.1fr) minmax(240px, 1fr) minmax(220px, 0.95fr)',
                gap: '1.25rem',
                alignItems: 'stretch',
              }}>
                {/* 1. Driver Live Video Card with green "Live" badge */}
                <div>
                  <CameraFeed visionData={statusData?.vision} compact={true} />
                </div>

                {/* 2. Semicircular Radial Gauge for Risk Score */}
                <div>
                  <RiskGaugeCard riskState={statusData?.risk_state} />
                </div>

                {/* 3. Stacked Biometric Mini-Cards (Heart Rate + HRV) */}
                <div>
                  <BiometricMetricsCard
                    sensorData={statusData?.sensor}
                    onOpenBoultModal={() => setShowBoultModal(true)}
                    onOpenHealthModal={() => setShowHealthModal(true)}
                    onInjectBpm={handleInjectBpm}
                  />
                </div>
              </div>

              {/* BOTTOM TIER: Wide Trip Timeline Graph (Risk Score, Heart Rate, EAR) */}
              <div>
                <TripTimelineChart
                  currentRisk={statusData?.risk_state?.risk_score}
                  currentHr={statusData?.sensor?.heart_rate_bpm}
                  currentEar={statusData?.vision?.ear_score}
                />
              </div>

              {/* Cockpit Quick-Action Simulation Toolbar */}
              <div style={{
                background: 'rgba(15, 23, 42, 0.65)',
                border: '1px solid rgba(255, 255, 255, 0.06)',
                borderRadius: '14px',
                padding: '0.75rem 1.15rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '0.75rem',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                  <span style={{ fontSize: '0.74rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase' }}>
                    🧪 Biometric Simulator:
                  </span>
                  <button onClick={() => handleInjectBpm(74.0, 'simulated_normal', SensorDataStatus.SIMULATED_DEMO)} className="btn btn-chip" style={{ color: '#10b981' }}>
                    💚 Normal (74)
                  </button>
                  <button onClick={() => handleInjectBpm(48.0, 'simulated_drowsy', SensorDataStatus.SIMULATED_DEMO)} className="btn btn-chip" style={{ color: '#f59e0b' }}>
                    ⚠️ Drowsy (48)
                  </button>
                  <button onClick={() => handleInjectBpm(122.0, 'simulated_panic', SensorDataStatus.SIMULATED_DEMO)} className="btn btn-chip" style={{ color: '#ef4444' }}>
                    🚨 Panic (122)
                  </button>
                  <button onClick={() => handleInjectBpm(72.0, 'simulated_stale', SensorDataStatus.STALE_DATA)} className="btn btn-chip" style={{ color: '#f59e0b' }}>
                    ⏳ Stale (25s)
                  </button>
                  <button onClick={() => handleInjectBpm(null, 'none', SensorDataStatus.UNAVAILABLE)} className="btn btn-chip" style={{ color: '#64748b' }}>
                    ❌ Off
                  </button>
                </div>

                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                  <button onClick={() => setShowNetworkModal(true)} className="btn btn-secondary" style={{ fontSize: '0.74rem', padding: '0.35rem 0.65rem' }}>
                    📱 Mobile Sync IP
                  </button>
                  <button onClick={() => setShowGpsModal(true)} className="btn btn-secondary" style={{ fontSize: '0.74rem', padding: '0.35rem 0.65rem' }}>
                    📍 GPS Setup
                  </button>
                </div>
              </div>
            </>
          )}

          {/* TAB 2: LIVE VIDEO (Full-screen Camera & FaceMesh Diagnostic) */}
          {activeTab === 'video' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <CameraFeed visionData={statusData?.vision} compact={false} />
            </div>
          )}

          {/* TAB 3: HEALTH DATA (Boult Watch BLE, Google Health Connect, Vitals) */}
          {activeTab === 'health' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <SensorCard
                sensorData={statusData?.sensor}
                gpsData={statusData?.gps}
                escalationData={statusData?.escalation}
                sessionActive={isActive}
              />
            </div>
          )}

          {/* TAB 4: TRIP HISTORY (Event & Alert Audit Log) */}
          {activeTab === 'history' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <EventHistory events={alerts} />
            </div>
          )}

          {/* TAB 5: ALERTS & SAFETY ESCALATION */}
          {activeTab === 'alerts' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <RiskCard riskState={statusData?.risk_state} />
              <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc' }}>
                    Safety Escalation Protocol & SMS Dispatcher
                  </h3>
                  <button onClick={() => setShowContactModal(true)} className="btn btn-secondary" style={{ fontSize: '0.75rem' }}>
                    ✏️ Edit Emergency Contact
                  </button>
                </div>
                <div style={{ fontSize: '0.85rem', color: '#cbd5e1', lineHeight: 1.6 }}>
                  <p>
                    When drowsiness persists, the cabin buzzer escalates frequencies (1500 Hz → 2500 Hz). The driver is given a 10-second grace window to acknowledge before an automated emergency SMS with live GPS coordinates is dispatched to family.
                  </p>
                  <div style={{ marginTop: '0.75rem', display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
                    <div>
                      <span style={{ color: '#94a3b8' }}>Contact: </span>
                      <strong>{statusData?.escalation?.emergency_contact_phone || '+919876543210'}</strong>
                    </div>
                    <div>
                      <span style={{ color: '#94a3b8' }}>Current Stage: </span>
                      <strong>{statusData?.escalation?.stage || 'MONITORING'}</strong>
                    </div>
                    <div>
                      <span style={{ color: '#94a3b8' }}>SMS Provider: </span>
                      <strong style={{ color: '#38bdf8' }}>Mock Sender (Safe Mode)</strong>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 6: SETTINGS (Network, Android Webhooks, Twilio Config) */}
          {activeTab === 'settings' && (
            <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>
                System & Connectivity Configuration
              </h3>

              <div className="inner-panel" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <h4 style={{ fontSize: '0.9rem', color: '#38bdf8' }}>📱 Mobile Android Synchronization</h4>
                <p style={{ fontSize: '0.82rem', color: '#cbd5e1' }}>
                  Laptop LAN IP address for Android GPS Logger / MacroDroid stream:
                </p>
                <code style={{ background: '#020617', padding: '0.6rem 0.85rem', borderRadius: '8px', color: '#38bdf8', fontFamily: 'var(--font-mono)', fontSize: '0.82rem' }}>
                  {networkInfo?.primary_ip || '127.0.0.1'}
                </code>
              </div>

              <div className="inner-panel" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <h4 style={{ fontSize: '0.9rem', color: '#38bdf8' }}>📍 GPS Ingestion Webhook</h4>
                <code style={{ background: '#020617', padding: '0.6rem 0.85rem', borderRadius: '8px', color: '#38bdf8', fontFamily: 'var(--font-mono)', fontSize: '0.82rem' }}>
                  {fallbackGpsWebhook}
                </code>
              </div>

              <div className="inner-panel" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <h4 style={{ fontSize: '0.9rem', color: '#38bdf8' }}>🩺 Google Health Connect Webhook</h4>
                <code style={{ background: '#020617', padding: '0.6rem 0.85rem', borderRadius: '8px', color: '#38bdf8', fontFamily: 'var(--font-mono)', fontSize: '0.82rem' }}>
                  {fallbackHealthWebhook}
                </code>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* PORTAL MODALS */}

      {/* Modal 1: Mobile Sync IP Modal */}
      {showNetworkModal && ReactDOM.createPortal(
        <div className="modal-overlay" onClick={() => setShowNetworkModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1.25rem 1.5rem', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <span style={{ fontSize: '1.2rem' }}>📱</span>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>Mobile Device Synchronization</h3>
              </div>
              <button onClick={() => setShowNetworkModal(false)} style={{ background: 'transparent', border: 'none', color: '#94a3b8', fontSize: '1.5rem', cursor: 'pointer', lineHeight: 1 }}>×</button>
            </div>
            <div style={{ padding: '1.5rem', overflowY: 'auto', fontSize: '0.85rem', color: '#cbd5e1', lineHeight: 1.6, display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <p>Connect your Android phone to stream GPS coordinates or Health Connect heart rate over Wi-Fi.</p>
              <div>
                <strong>Laptop LAN IP:</strong>
                <code style={{ display: 'block', background: '#020617', padding: '0.6rem 0.85rem', borderRadius: '8px', color: '#38bdf8', fontFamily: 'var(--font-mono)', marginTop: '0.35rem' }}>
                  {networkInfo?.primary_ip || '127.0.0.1'}
                </code>
              </div>
              <div>
                <strong>Android GPS Webhook URL:</strong>
                <code style={{ display: 'block', background: '#020617', padding: '0.6rem 0.85rem', borderRadius: '8px', color: '#38bdf8', fontFamily: 'var(--font-mono)', marginTop: '0.35rem' }}>
                  {fallbackGpsWebhook}
                </code>
              </div>
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', padding: '1rem 1.5rem', borderTop: '1px solid rgba(255,255,255,0.08)' }}>
              <button onClick={() => setShowNetworkModal(false)} className="btn btn-primary">Done</button>
            </div>
          </div>
        </div>,
        document.body
      )}

      {/* Modal 2: Boult Compatibility Audit */}
      {showBoultModal && ReactDOM.createPortal(
        <div className="modal-overlay" onClick={() => setShowBoultModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1.25rem 1.5rem', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <span style={{ fontSize: '1.2rem' }}>🔍</span>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>Boult Smartwatch Compatibility Audit</h3>
              </div>
              <button onClick={() => setShowBoultModal(false)} style={{ background: 'transparent', border: 'none', color: '#94a3b8', fontSize: '1.5rem', cursor: 'pointer' }}>×</button>
            </div>
            <div style={{ padding: '1.5rem', overflowY: 'auto', fontSize: '0.85rem', color: '#cbd5e1', lineHeight: 1.6, display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ background: 'rgba(239, 68, 68, 0.1)', borderLeft: '3px solid #ef4444', padding: '0.85rem 1rem', borderRadius: '8px' }}>
                <strong style={{ color: '#fca5a5' }}>Architectural Reality Notice:</strong> Boult consumer watches (Drift, Striker, Crown, Ridge) pair with proprietary apps (Boult Fit / Da Fit) and do not publish an open vendor cloud API. Direct BLE requires Heart Rate Service <code>0x180D</code>.
              </div>
              <div>
                <strong style={{ color: '#f8fafc' }}>Verification Steps on Android:</strong>
                <ol style={{ paddingLeft: '1.25rem', marginTop: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                  <li>Install <strong>nRF Connect for Mobile</strong> from Google Play.</li>
                  <li>Disconnect watch from Boult Fit app temporarily.</li>
                  <li>Scan and connect to watch. Look for Service <code>0x180D (Heart Rate)</code>.</li>
                  <li>If 0x180D is absent, use the <strong>Google Health Connect</strong> or <strong>Health Sync</strong> bridge.</li>
                </ol>
              </div>
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', padding: '1rem 1.5rem', borderTop: '1px solid rgba(255,255,255,0.08)' }}>
              <button onClick={() => setShowBoultModal(false)} className="btn btn-primary">Done</button>
            </div>
          </div>
        </div>,
        document.body
      )}

      {/* Modal 3: Health Connect Setup */}
      {showHealthModal && ReactDOM.createPortal(
        <div className="modal-overlay" onClick={() => setShowHealthModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1.25rem 1.5rem', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <span style={{ fontSize: '1.2rem' }}>🔗</span>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>Health Connect Mobile Webhook</h3>
              </div>
              <button onClick={() => setShowHealthModal(false)} style={{ background: 'transparent', border: 'none', color: '#94a3b8', fontSize: '1.5rem', cursor: 'pointer' }}>×</button>
            </div>
            <div style={{ padding: '1.5rem', overflowY: 'auto', fontSize: '0.85rem', color: '#cbd5e1', lineHeight: 1.6, display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <p>Push real-time heart rate from your Android phone directly to this laptop over Wi-Fi.</p>
              <div>
                <strong>Webhook Target URL:</strong>
                <div style={{ display: 'flex', alignItems: 'center', background: '#020617', padding: '0.6rem 0.85rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)', marginTop: '0.35rem', fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: '#38bdf8' }}>
                  <span style={{ flex: 1, wordBreak: 'break-all' }}>{fallbackHealthWebhook}</span>
                  <button onClick={() => copyToClipboard(fallbackHealthWebhook, 'health')} className="btn btn-secondary" style={{ padding: '0.25rem 0.6rem', fontSize: '0.75rem', marginLeft: '0.5rem' }}>
                    {copiedKey === 'health' ? '✓ Copied' : 'Copy'}
                  </button>
                </div>
              </div>
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', padding: '1rem 1.5rem', borderTop: '1px solid rgba(255,255,255,0.08)' }}>
              <button onClick={() => setShowHealthModal(false)} className="btn btn-primary">Done</button>
            </div>
          </div>
        </div>,
        document.body
      )}

      {/* Modal 4: GPS Setup */}
      {showGpsModal && ReactDOM.createPortal(
        <div className="modal-overlay" onClick={() => setShowGpsModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1.25rem 1.5rem', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <span style={{ fontSize: '1.2rem' }}>📍</span>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>Android GPS Webhook Setup</h3>
              </div>
              <button onClick={() => setShowGpsModal(false)} style={{ background: 'transparent', border: 'none', color: '#94a3b8', fontSize: '1.5rem', cursor: 'pointer' }}>×</button>
            </div>
            <div style={{ padding: '1.5rem', overflowY: 'auto', fontSize: '0.85rem', color: '#cbd5e1', lineHeight: 1.6, display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <strong>Android GPS Webhook URL:</strong>
                <div style={{ display: 'flex', alignItems: 'center', background: '#020617', padding: '0.6rem 0.85rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)', marginTop: '0.35rem', fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: '#38bdf8' }}>
                  <span style={{ flex: 1, wordBreak: 'break-all' }}>{fallbackGpsWebhook}</span>
                  <button onClick={() => copyToClipboard(fallbackGpsWebhook, 'gps')} className="btn btn-secondary" style={{ padding: '0.25rem 0.6rem', fontSize: '0.75rem', marginLeft: '0.5rem' }}>
                    {copiedKey === 'gps' ? '✓ Copied' : 'Copy'}
                  </button>
                </div>
              </div>
              <div>
                <strong>Automation Options:</strong>
                <ul style={{ paddingLeft: '1.25rem', marginTop: '0.35rem', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                  <li><strong>Option 1: GPS Logger for Android</strong>. Set Custom URL to the POST webhook above.</li>
                  <li><strong>Option 2: MacroDroid / Tasker</strong>. Action: HTTP POST coordinates on location update.</li>
                </ul>
              </div>
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', padding: '1rem 1.5rem', borderTop: '1px solid rgba(255,255,255,0.08)' }}>
              <button onClick={() => setShowGpsModal(false)} className="btn btn-primary">Done</button>
            </div>
          </div>
        </div>,
        document.body
      )}

      {/* Modal 5: Edit Contact */}
      {showContactModal && ReactDOM.createPortal(
        <div className="modal-overlay" onClick={() => setShowContactModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1.25rem 1.5rem', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <span style={{ fontSize: '1.2rem' }}>✏️</span>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>Configure Emergency Contact</h3>
              </div>
              <button onClick={() => setShowContactModal(false)} style={{ background: 'transparent', border: 'none', color: '#94a3b8', fontSize: '1.5rem', cursor: 'pointer' }}>×</button>
            </div>
            <div style={{ padding: '1.5rem', fontSize: '0.85rem', color: '#cbd5e1', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', color: '#94a3b8', marginBottom: '0.35rem' }}>Contact Name</label>
                <input
                  type="text"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  style={{ width: '100%', background: '#020617', border: '1px solid rgba(255,255,255,0.15)', borderRadius: '8px', padding: '0.6rem 0.85rem', color: '#f8fafc', fontSize: '0.88rem' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', color: '#94a3b8', marginBottom: '0.35rem' }}>Phone Number (with country code)</label>
                <input
                  type="text"
                  value={newPhone}
                  onChange={(e) => setNewPhone(e.target.value)}
                  style={{ width: '100%', background: '#020617', border: '1px solid rgba(255,255,255,0.15)', borderRadius: '8px', padding: '0.6rem 0.85rem', color: '#f8fafc', fontSize: '0.88rem' }}
                />
              </div>
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.6rem', padding: '1rem 1.5rem', borderTop: '1px solid rgba(255,255,255,0.08)' }}>
              <button onClick={() => setShowContactModal(false)} className="btn btn-secondary">Cancel</button>
              <button onClick={handleSaveContact} className="btn btn-primary">Save Contact</button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </div>
  );
}
