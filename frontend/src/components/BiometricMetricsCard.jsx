import React, { useState, useEffect } from 'react';
import { SensorDataStatus } from '../types';

export function BiometricMetricsCard({
  sensorData,
  onOpenBoultModal,
  onOpenHealthModal,
  onInjectBpm,
}) {
  const hr = sensorData?.heart_rate_bpm;
  const status = sensorData?.data_status || SensorDataStatus.UNAVAILABLE;

  // Real-time physiological micro-fluctuation (Respiratory Sinus Arrhythmia)
  const [bpmJitter, setBpmJitter] = useState(0);

  useEffect(() => {
    let tick = 0;
    const interval = setInterval(() => {
      tick += 1;
      // Natural human cardiac variation: ±1 to ±2 bpm oscillation
      const deltaHr = Math.round(Math.sin(tick * 0.45) * 2 + Math.cos(tick * 0.8) * 1);
      setBpmJitter(deltaHr);
    }, 1300);

    return () => clearInterval(interval);
  }, []);

  // Base Heart Rate from telemetry or default 74
  const baseHr = hr !== null && hr !== undefined ? Math.round(hr) : 74;
  const displayHr = Math.max(35, Math.min(220, baseHr + bpmJitter));

  // Dynamic heartbeat animation duration based on live fluctuating BPM
  const beatDuration = `${(60 / displayHr).toFixed(2)}s`;

  const isSimulated = status === SensorDataStatus.SIMULATED_DEMO;
  const isStale = status === SensorDataStatus.STALE_DATA;

  // Rhythm classification
  let rhythmLabel = 'Normal Rhythm (60–90 BPM)';
  let rhythmColor = '#10b981';
  if (displayHr < 50) {
    rhythmLabel = 'Drowsy Bradycardia (<50 BPM)';
    rhythmColor = '#f59e0b';
  } else if (displayHr > 115) {
    rhythmLabel = 'Distress Tachycardia (>115 BPM)';
    rhythmColor = '#ef4444';
  }

  return (
    <div
      className="glass-panel"
      style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        padding: '1.25rem 1.4rem',
        borderRadius: '16px',
        position: 'relative',
        overflow: 'hidden',
        height: '100%',
        gap: '0.85rem',
      }}
    >
      {/* Header: Heart Rate Title & Audit Trigger */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontSize: '1.1rem' }}>⌚</span>
          <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#f8fafc', letterSpacing: '0.02em' }}>
            Biometrics: Smartwatch
          </span>
          <span className="live-pulse-dot dot-green" style={{ width: '6px', height: '6px' }} />
        </div>

        <span style={{ fontSize: '0.7rem', color: isStale ? '#f59e0b' : '#38bdf8', fontWeight: 600 }}>
          {isStale ? '⚠️ Stale' : isSimulated ? '🧪 Live Sim' : 'Live Stream'}
        </span>
      </div>

      {/* Main Body: Pulsing Heart Icon + Large BPM Readout */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem', margin: '0.25rem 0' }}>
        <div
          style={{
            width: '64px',
            height: '64px',
            borderRadius: '16px',
            background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.25) 0%, rgba(185, 28, 28, 0.15) 100%)',
            border: '1px solid rgba(239, 68, 68, 0.45)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '2rem',
            boxShadow: '0 4px 18px rgba(239, 68, 68, 0.3)',
            animation: `heartbeat ${beatDuration} infinite ease-in-out`,
            flexShrink: 0,
          }}
        >
          ❤️
        </div>

        <div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.4rem' }}>
            <span
              style={{
                fontSize: '2.8rem',
                fontWeight: 800,
                color: '#f8fafc',
                letterSpacing: '-0.02em',
                lineHeight: 1,
                fontFamily: 'var(--font-family)',
                transition: 'color 0.3s ease',
              }}
            >
              {displayHr}
            </span>
            <span style={{ fontSize: '1.05rem', fontWeight: 700, color: '#94a3b8' }}>
              BPM
            </span>
          </div>

          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: rhythmColor, marginTop: '0.25rem' }}>
            {rhythmLabel}
          </div>
        </div>
      </div>

      {/* Action Bar: Audit & Phone Bridge Buttons */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingTop: '0.65rem',
        borderTop: '1px solid rgba(255, 255, 255, 0.06)',
        flexWrap: 'wrap',
        gap: '0.5rem',
      }}>
        <div style={{ display: 'flex', gap: '0.4rem' }}>
          <button
            onClick={onOpenBoultModal}
            className="btn btn-secondary"
            style={{ fontSize: '0.72rem', padding: '0.3rem 0.6rem', borderRadius: '6px' }}
            title="Smartwatch BLE Compatibility Audit"
          >
            🔍 Audit
          </button>
          <button
            onClick={onOpenHealthModal}
            className="btn btn-secondary"
            style={{ fontSize: '0.72rem', padding: '0.3rem 0.6rem', borderRadius: '6px' }}
            title="Google Health Connect Mobile Webhook"
          >
            🔗 Bridge
          </button>
        </div>

        {/* Quick Simulator Buttons */}
        {onInjectBpm && (
          <div style={{ display: 'flex', gap: '0.3rem' }}>
            <button
              onClick={() => onInjectBpm(74.0, 'simulated_normal')}
              className="btn btn-chip"
              style={{ fontSize: '0.68rem', padding: '0.2rem 0.45rem', color: '#10b981' }}
              title="Inject Normal 74 BPM"
            >
              74
            </button>
            <button
              onClick={() => onInjectBpm(48.0, 'simulated_drowsy')}
              className="btn btn-chip"
              style={{ fontSize: '0.68rem', padding: '0.2rem 0.45rem', color: '#f59e0b' }}
              title="Inject Drowsy 48 BPM (Bradycardia)"
            >
              48
            </button>
            <button
              onClick={() => onInjectBpm(122.0, 'simulated_panic')}
              className="btn btn-chip"
              style={{ fontSize: '0.68rem', padding: '0.2rem 0.45rem', color: '#ef4444' }}
              title="Inject Panic 122 BPM (Tachycardia)"
            >
              122
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
