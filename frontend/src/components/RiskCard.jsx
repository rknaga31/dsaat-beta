import React from 'react';
import { RiskState } from '../types';

function cleanReason(reason) {
  if (!reason) return '';
  return reason.replace(/\(\d+\.?\d*s old\)/g, '(stale)');
}

export function RiskCard({ riskState }) {
  const score = riskState?.risk_score ?? 0;
  const state = riskState?.state ?? RiskState.MONITORING_UNAVAILABLE;
  const reliable = riskState?.monitoring_reliable ?? false;
  const reasons = (riskState?.contributing_reasons ?? []).map(cleanReason);

  const getBadgeClass = () => {
    switch (state) {
      case RiskState.NORMAL: return 'badge-normal';
      case RiskState.WARNING: return 'badge-warning';
      case RiskState.HIGH_RISK: return 'badge-danger';
      default: return 'badge-muted';
    }
  };

  const getScoreColor = () => {
    if (score >= 80) return '#ef4444';
    if (score >= 40) return '#f59e0b';
    return '#10b981';
  };

  const getScoreGradient = () => {
    if (score >= 80) return 'linear-gradient(90deg, #f59e0b 0%, #ef4444 100%)';
    if (score >= 40) return 'linear-gradient(90deg, #10b981 0%, #f59e0b 100%)';
    return 'linear-gradient(90deg, #059669 0%, #10b981 100%)';
  };

  return (
    <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '1.15rem' }}>
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontSize: '1.1rem' }}>⚡</span>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc', letterSpacing: '-0.01em' }}>
            Multimodal Fusion Risk State
          </h3>
        </div>
        <span className={`badge ${getBadgeClass()}`}>{state.replace(/_/g, ' ')}</span>
      </div>

      {/* Main Score Readout */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: 'rgba(2, 6, 23, 0.45)',
        padding: '0.85rem 1.15rem',
        borderRadius: '12px',
        border: '1px solid rgba(255,255,255,0.06)',
      }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem' }}>
          <span style={{
            fontSize: '2.6rem',
            fontWeight: 800,
            color: getScoreColor(),
            lineHeight: 1,
            fontFamily: 'var(--font-mono)',
          }}>
            {score.toFixed(1)}
          </span>
          <span style={{ color: 'var(--text-dim)', fontSize: '0.95rem', fontWeight: 600 }}>/ 100</span>
        </div>

        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Tracking Integrity
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', justifyContent: 'flex-end', marginTop: '0.2rem' }}>
            <span className={`live-pulse-dot ${reliable ? 'dot-green' : 'dot-red'}`} />
            <strong style={{ fontSize: '0.85rem', color: reliable ? '#10b981' : '#f59e0b' }}>
              {reliable ? 'High Confidence' : 'Degraded Telemetry'}
            </strong>
          </div>
        </div>
      </div>

      {/* Precision Progress Bar */}
      <div>
        <div style={{
          width: '100%',
          height: '7px',
          background: 'rgba(255,255,255,0.06)',
          borderRadius: '9999px',
          overflow: 'hidden',
          position: 'relative',
        }}>
          <div style={{
            width: `${Math.min(Math.max(score, 0), 100)}%`,
            height: '100%',
            background: getScoreGradient(),
            borderRadius: '9999px',
            boxShadow: `0 0 10px ${getScoreColor()}`,
            transition: 'width 0.5s cubic-bezier(0.16, 1, 0.3, 1), background 0.5s ease',
          }} />
        </div>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          fontSize: '0.68rem',
          color: 'var(--text-dim)',
          marginTop: '0.35rem',
          fontWeight: 600,
        }}>
          <span>NORMAL (0-39)</span>
          <span>ELEVATED (40-79)</span>
          <span>CRITICAL (80-100)</span>
        </div>
      </div>

      {/* Contributing Rationale Feed */}
      <div className="inner-panel">
        <div style={{
          fontSize: '0.72rem',
          fontWeight: 700,
          color: '#94a3b8',
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
          marginBottom: '0.5rem',
        }}>
          Contributing Risk Telemetry
        </div>

        {reasons.length > 0 ? (
          <ul style={{ listStyleType: 'none', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
            {reasons.map((r, idx) => (
              <li key={idx} style={{
                fontSize: '0.82rem',
                color: '#cbd5e1',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '0.45rem',
              }}>
                <span style={{ color: getScoreColor(), fontSize: '0.9rem', lineHeight: '1.2' }}>•</span>
                <span>{r}</span>
              </li>
            ))}
          </ul>
        ) : (
          <div style={{ fontSize: '0.82rem', color: '#64748b', fontStyle: 'italic' }}>
            Baseline steady • No anomalous fatigue or physiological patterns detected
          </div>
        )}
      </div>
    </div>
  );
}
