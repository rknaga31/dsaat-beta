import React from 'react';
import { RiskState, SmsStatus } from '../types';

function cleanReason(reason) {
  if (!reason) return '';
  // Clean raw float seconds like "1766.1s old" to cleaner text
  return reason.replace(/\(\d+\.?\d*s old\)/g, '(stale)');
}

export function AlertBanner({ riskState, activeAlert, escalation, onAcknowledge }) {
  if (!riskState && !activeAlert) {
    return null;
  }

  const state = riskState?.state;
  const isNormal = state === RiskState.NORMAL && (!activeAlert || activeAlert.alert_level === 'INFO');
  if (isNormal) {
    return null;
  }

  const isUnavailable = state === RiskState.MONITORING_UNAVAILABLE;
  const isWarning = state === RiskState.WARNING;
  const isCritical = state === RiskState.HIGH_RISK || activeAlert?.alert_level === 'CRITICAL';

  const isPending = escalation?.is_pending || activeAlert?.family_sms_status === SmsStatus.ESCALATION_PENDING;
  const remainingSec = escalation?.remaining_ack_seconds ?? 0;
  const smsSent = activeAlert?.family_sms_status === SmsStatus.SENT || activeAlert?.family_sms_status === SmsStatus.MOCK_SENT;

  if (isUnavailable) {
    return (
      <div style={{
        background: 'rgba(15, 23, 42, 0.85)',
        border: '1px solid rgba(148, 163, 184, 0.3)',
        borderRadius: '14px',
        padding: '1rem 1.4rem',
        marginBottom: '1.25rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '0.9rem',
        boxShadow: 'var(--shadow-sm)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '10px',
            background: 'rgba(100, 116, 139, 0.2)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.25rem',
          }}>
            ⚠️
          </div>
          <div>
            <div style={{ fontWeight: 700, color: '#f8fafc', fontSize: '0.95rem' }}>
              Monitoring Telemetry Standby / Unavailable
            </div>
            <div style={{ fontSize: '0.82rem', color: '#94a3b8', marginTop: '0.15rem' }}>
              {riskState?.contributing_reasons?.map(cleanReason).join(' • ') || 'Awaiting camera facial lock or sensor telemetry stream...'}
            </div>
          </div>
        </div>
        <span className="badge badge-warning">INFO CHIME ACTIVE</span>
      </div>
    );
  }

  if (isPending) {
    return (
      <div style={{
        background: 'linear-gradient(135deg, rgba(153, 27, 27, 0.45) 0%, rgba(69, 10, 10, 0.55) 100%)',
        border: '2px solid #ef4444',
        boxShadow: '0 0 35px rgba(239, 68, 68, 0.45)',
        borderRadius: '16px',
        padding: '1.2rem 1.5rem',
        marginBottom: '1.4rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1.2rem',
        animation: 'pulse-danger 1.8s infinite',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.15rem' }}>
          <div style={{
            width: '54px',
            height: '54px',
            borderRadius: '14px',
            background: 'rgba(239, 68, 68, 0.25)',
            border: '1px solid rgba(239, 68, 68, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.75rem',
          }}>
            🚨
          </div>
          <div>
            <div style={{
              fontSize: '1.15rem',
              fontWeight: 800,
              color: '#fef2f2',
              letterSpacing: '-0.01em',
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem',
              flexWrap: 'wrap',
            }}>
              <span>CRITICAL DROWSINESS ESCALATION</span>
              <span style={{
                background: '#dc2626',
                color: '#fff',
                padding: '0.25rem 0.65rem',
                borderRadius: '8px',
                fontSize: '0.8rem',
                fontWeight: 800,
                letterSpacing: '0.04em',
                boxShadow: '0 2px 8px rgba(0,0,0,0.4)',
              }}>
                DISPATCHING FAMILY SOS IN {remainingSec}s
              </span>
            </div>
            <div style={{ fontSize: '0.85rem', color: '#fca5a5', marginTop: '0.35rem' }}>
              Driver must tap below immediately to confirm alertness, silence audio alarm, and cancel family notification.
            </div>
          </div>
        </div>

        <button
          onClick={onAcknowledge}
          className="btn btn-danger"
          style={{
            padding: '0.75rem 1.4rem',
            fontSize: '0.95rem',
            fontWeight: 700,
            borderRadius: '12px',
            border: '1px solid #fca5a5',
          }}
        >
          🛑 I Am Awake — Silence Buzzer & Cancel SMS
        </button>
      </div>
    );
  }

  return (
    <div style={{
      background: isCritical
        ? 'linear-gradient(135deg, rgba(127, 29, 29, 0.35) 0%, rgba(69, 10, 10, 0.45) 100%)'
        : 'linear-gradient(135deg, rgba(120, 53, 15, 0.35) 0%, rgba(67, 20, 7, 0.45) 100%)',
      border: `1px solid ${isCritical ? 'rgba(239, 68, 68, 0.6)' : 'rgba(245, 158, 11, 0.5)'}`,
      boxShadow: isCritical ? 'var(--shadow-glow-danger)' : 'none',
      borderRadius: '14px',
      padding: '1.1rem 1.4rem',
      marginBottom: '1.25rem',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      flexWrap: 'wrap',
      gap: '1rem',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div style={{
          width: '46px',
          height: '46px',
          borderRadius: '12px',
          background: isCritical ? 'rgba(239, 68, 68, 0.2)' : 'rgba(245, 158, 11, 0.2)',
          border: `1px solid ${isCritical ? 'rgba(239, 68, 68, 0.4)' : 'rgba(245, 158, 11, 0.4)'}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '1.5rem',
        }}>
          {isCritical ? '🚨' : '⚠️'}
        </div>
        <div>
          <div style={{
            fontSize: '1.05rem',
            fontWeight: 800,
            color: isCritical ? '#fecaca' : '#fef3c7',
            letterSpacing: '0.01em',
          }}>
            {isCritical ? 'CRITICAL DROWSINESS / HEALTH ALERT' : 'WARNING: DRIVER FATIGUE DETECTED'}
          </div>
          <div style={{ fontSize: '0.84rem', color: '#cbd5e1', marginTop: '0.2rem' }}>
            {riskState?.contributing_reasons?.map(cleanReason).join(' • ') || 'Please pull over safely and take a rest.'}
          </div>
          {smsSent && (
            <div style={{
              fontSize: '0.8rem',
              color: '#38bdf8',
              marginTop: '0.35rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              fontWeight: 500,
            }}>
              <span>📱</span>
              <span>
                Family SOS dispatched ({activeAlert.family_sms_status}) to registered contact: {escalation?.emergency_contact_phone || 'Emergency Contact'}
              </span>
            </div>
          )}
        </div>
      </div>

      <div>
        <button
          onClick={onAcknowledge}
          className="btn btn-secondary"
          style={{ background: 'rgba(0,0,0,0.4)', borderColor: 'rgba(255,255,255,0.2)' }}
        >
          Silence Buzzer
        </button>
      </div>
    </div>
  );
}
