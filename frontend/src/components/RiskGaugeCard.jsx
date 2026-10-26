import React from 'react';
import { RiskState } from '../types';

export function RiskGaugeCard({ riskState }) {
  const score = Math.round(riskState?.risk_score ?? 25);
  const state = riskState?.state ?? RiskState.NORMAL;

  // Gauge parameters for an arc from -110 deg to +110 deg (220 degrees total)
  const radius = 78;
  const strokeWidth = 14;
  const circumference = Math.PI * radius * (220 / 180);
  const normalizedScore = Math.min(Math.max(score, 0), 100);
  const strokeDashoffset = circumference - (normalizedScore / 100) * circumference;

  // Calculate tip indicator dot position
  const angleDeg = -110 + (220 * (normalizedScore / 100));
  const angleRad = (angleDeg - 90) * (Math.PI / 180);
  const tipX = 100 + radius * Math.cos(angleRad);
  const tipY = 115 + radius * Math.sin(angleRad);

  const getColor = () => {
    if (score >= 80) return '#ef4444';
    if (score >= 40) return '#f59e0b';
    return '#10b981';
  };

  const getStatusText = () => {
    if (state === RiskState.HIGH_RISK || score >= 80) return 'HIGH RISK';
    if (state === RiskState.WARNING || score >= 40) return 'WARNING';
    if (state === RiskState.MONITORING_UNAVAILABLE) return 'STANDBY';
    return 'NORMAL';
  };

  const getPillBg = () => {
    if (score >= 80) return 'linear-gradient(135deg, #dc2626 0%, #b91c1c 100%)';
    if (score >= 40) return 'linear-gradient(135deg, #d97706 0%, #b45309 100%)';
    return 'linear-gradient(135deg, #059669 0%, #047857 100%)';
  };

  const getPillShadow = () => {
    if (score >= 80) return '0 4px 18px rgba(239, 68, 68, 0.4)';
    if (score >= 40) return '0 4px 18px rgba(245, 158, 11, 0.4)';
    return '0 4px 18px rgba(16, 185, 129, 0.4)';
  };

  return (
    <div className="glass-panel" style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '1.4rem 1.25rem',
      position: 'relative',
      minHeight: '260px',
      height: '100%',
    }}>
      {/* Gauge Semicircle SVG */}
      <div style={{ position: 'relative', width: '200px', height: '150px', marginTop: '0.25rem' }}>
        <svg
          viewBox="0 0 200 160"
          style={{ width: '100%', height: '100%', overflow: 'visible' }}
        >
          <defs>
            <filter id="gaugeGlow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="4" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Background Track Arc */}
          <path
            d="M 27 135 A 78 78 0 1 1 173 135"
            fill="none"
            stroke="rgba(255, 255, 255, 0.08)"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />

          {/* Active Progress Arc */}
          <path
            d="M 27 135 A 78 78 0 1 1 173 135"
            fill="none"
            stroke={getColor()}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            filter="url(#gaugeGlow)"
            style={{
              transition: 'stroke-dashoffset 0.6s cubic-bezier(0.16, 1, 0.3, 1), stroke 0.4s ease',
            }}
          />

          {/* Active Tip Indicator Dot matching reference image */}
          <circle
            cx={tipX}
            cy={tipY}
            r="6"
            fill={getColor()}
            stroke="#ffffff"
            strokeWidth="2"
            filter="url(#gaugeGlow)"
            style={{
              transition: 'cx 0.6s cubic-bezier(0.16, 1, 0.3, 1), cy 0.6s cubic-bezier(0.16, 1, 0.3, 1)',
            }}
          />

          {/* Subtle decorative tick marks */}
          <circle cx="27" cy="135" r="2.5" fill="#475569" />
          <circle cx="100" cy="37" r="2.5" fill="#475569" />
          <circle cx="173" cy="135" r="2.5" fill="#475569" />
        </svg>

        {/* Center Numbers and Labels */}
        <div style={{
          position: 'absolute',
          top: '46px',
          left: 0,
          right: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          textAlign: 'center',
        }}>
          <span style={{
            fontSize: '3.1rem',
            fontWeight: 800,
            color: '#f8fafc',
            lineHeight: 1,
            letterSpacing: '-0.03em',
            fontFamily: 'var(--font-family)',
            textShadow: `0 0 20px ${getColor()}40`,
          }}>
            {score}
          </span>
          <span style={{
            fontSize: '0.74rem',
            fontWeight: 700,
            color: '#94a3b8',
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            marginTop: '0.35rem',
          }}>
            RISK SCORE
          </span>
        </div>
      </div>

      {/* Pill Badge at bottom matching reference image */}
      <div style={{
        width: '84%',
        background: getPillBg(),
        color: '#ffffff',
        padding: '0.55rem 1rem',
        borderRadius: '9999px',
        textAlign: 'center',
        fontSize: '0.88rem',
        fontWeight: 800,
        letterSpacing: '0.06em',
        boxShadow: getPillShadow(),
        border: '1px solid rgba(255, 255, 255, 0.2)',
        marginTop: '0.5rem',
        transition: 'all 0.3s ease',
      }}>
        {getStatusText()}
      </div>
    </div>
  );
}
