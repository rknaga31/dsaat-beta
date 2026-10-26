import React, { useState, useEffect, useRef } from 'react';

// Generates an initial realistic 30-minute history curve matching the reference image
function generateInitialTimelinePoints() {
  const points = [];
  const now = Date.now();
  const sampleCount = 28;
  const stepMs = (30 * 60 * 1000) / sampleCount;

  for (let i = 0; i < sampleCount; i++) {
    const time = new Date(now - (sampleCount - 1 - i) * stepMs);
    // Smooth undulating wave equations
    const t = i / sampleCount;
    const hr = Math.round(72 + Math.sin(t * 8) * 8 + Math.cos(t * 14) * 4);
    const risk = Math.round(24 + Math.sin(t * 6 + 1.2) * 12 + (i > 18 ? Math.sin(t * 10) * 8 : 0));
    const ear = Math.round(32 + Math.sin(t * 9 + 0.5) * 8 + Math.cos(t * 5) * 4);

    points.push({
      time: time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      timestamp: time,
      hr: Math.max(45, Math.min(130, hr)),
      risk: Math.max(5, Math.min(95, risk)),
      ear: Math.max(10, Math.min(80, ear)),
    });
  }
  return points;
}

export function TripTimelineChart({ currentRisk, currentHr, currentEar }) {
  const [dataPoints, setDataPoints] = useState(generateInitialTimelinePoints);
  const [hoveredPoint, setHoveredPoint] = useState(null);
  const lastAddRef = useRef(Date.now());

  // Periodically append new live point as monitoring progresses
  useEffect(() => {
    const now = Date.now();
    // Throttle appends to every 5 seconds
    if (now - lastAddRef.current >= 5000) {
      lastAddRef.current = now;
      const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      const newPoint = {
        time: timeStr,
        timestamp: new Date(),
        hr: currentHr ? Math.round(currentHr) : 74,
        risk: currentRisk !== null && currentRisk !== undefined ? Math.round(currentRisk) : 25,
        ear: currentEar ? Math.round(currentEar * 100) : 32,
      };

      setDataPoints((prev) => {
        const next = [...prev.slice(1), newPoint];
        return next;
      });
    }
  }, [currentRisk, currentHr, currentEar]);

  // SVG Chart Geometry
  const width = 880;
  const height = 180;
  const paddingLeft = 45;
  const paddingRight = 25;
  const paddingTop = 20;
  const paddingBottom = 30;

  const chartWidth = width - paddingLeft - paddingRight;
  const chartHeight = height - paddingTop - paddingBottom;

  const getX = (index) => {
    return paddingLeft + (index / (dataPoints.length - 1)) * chartWidth;
  };

  const getY = (val) => {
    // Range 0 to 100
    const clamped = Math.max(0, Math.min(100, val));
    return paddingTop + chartHeight - (clamped / 100) * chartHeight;
  };

  // Build smooth Bézier SVG path
  const makeSmoothPath = (key) => {
    if (dataPoints.length === 0) return '';
    let d = `M ${getX(0)} ${getY(dataPoints[0][key])}`;
    for (let i = 0; i < dataPoints.length - 1; i++) {
      const x0 = getX(i);
      const y0 = getY(dataPoints[i][key]);
      const x1 = getX(i + 1);
      const y1 = getY(dataPoints[i + 1][key]);
      const mx = (x0 + x1) / 2;
      d += ` C ${mx} ${y0}, ${mx} ${y1}, ${x1} ${y1}`;
    }
    return d;
  };

  const hrPath = makeSmoothPath('hr');
  const riskPath = makeSmoothPath('risk');
  const earPath = makeSmoothPath('ear');

  // Key node indices to render highlight dots (every ~5th point)
  const dotIndices = [0, 5, 11, 16, 22, dataPoints.length - 1];

  // X-axis label points (4 intervals)
  const xLabels = [
    dataPoints[0]?.time || '09:50',
    dataPoints[Math.floor(dataPoints.length * 0.33)]?.time || '10:00',
    dataPoints[Math.floor(dataPoints.length * 0.66)]?.time || '10:10',
    dataPoints[dataPoints.length - 1]?.time || '10:20',
  ];

  return (
    <div className="glass-panel" style={{
      padding: '1.25rem 1.4rem',
      borderRadius: '18px',
      position: 'relative',
    }}>
      {/* Header: Title + Legend */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '0.85rem',
        flexWrap: 'wrap',
        gap: '0.75rem',
      }}>
        <h3 style={{
          fontSize: '1rem',
          fontWeight: 700,
          color: '#f8fafc',
          letterSpacing: '-0.01em',
        }}>
          Trip Timeline <span style={{ fontSize: '0.82rem', color: '#94a3b8', fontWeight: 500 }}>(Last 30 minutes)</span>
        </h3>

        {/* Legend matching reference image */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem', fontSize: '0.8rem', fontWeight: 600 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', color: '#f59e0b' }}>
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#f59e0b', display: 'inline-block' }} />
            <span>Risk Score</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', color: '#38bdf8' }}>
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#38bdf8', display: 'inline-block' }} />
            <span>Heart Rate</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', color: '#c084fc' }}>
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#c084fc', display: 'inline-block' }} />
            <span>EAR</span>
          </div>
        </div>
      </div>

      {/* Responsive SVG Chart */}
      <div style={{ width: '100%', position: 'relative' }}>
        <svg
          viewBox={`0 0 ${width} ${height}`}
          style={{ width: '100%', height: 'auto', display: 'block', overflow: 'visible' }}
          onMouseLeave={() => setHoveredPoint(null)}
        >
          <defs>
            {/* Glowing lines filter */}
            <filter id="lineGlowCyan" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="2.5" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
            <filter id="lineGlowAmber" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="2.5" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
            <filter id="lineGlowPurple" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="2.5" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Grid Lines: 100, 50, 0 */}
          {[100, 50, 0].map((val) => {
            const y = getY(val);
            return (
              <g key={val}>
                <line
                  x1={paddingLeft}
                  y1={y}
                  x2={width - paddingRight}
                  y2={y}
                  stroke="rgba(255, 255, 255, 0.08)"
                  strokeDasharray="4 4"
                  strokeWidth="1"
                />
                <text
                  x={paddingLeft - 10}
                  y={y + 4}
                  fill="#64748b"
                  fontSize="10"
                  fontFamily="var(--font-mono)"
                  textAnchor="end"
                >
                  {val}
                </text>
              </g>
            );
          })}

          {/* X and Y Baseline Axes */}
          <line
            x1={paddingLeft}
            y1={paddingTop}
            x2={paddingLeft}
            y2={paddingTop + chartHeight}
            stroke="rgba(255, 255, 255, 0.12)"
            strokeWidth="1.2"
          />
          <line
            x1={paddingLeft}
            y1={paddingTop + chartHeight}
            x2={width - paddingRight}
            y2={paddingTop + chartHeight}
            stroke="rgba(255, 255, 255, 0.12)"
            strokeWidth="1.2"
          />

          {/* 1. Heart Rate Curve (Cyan) */}
          <path
            d={hrPath}
            fill="none"
            stroke="#38bdf8"
            strokeWidth="2.4"
            filter="url(#lineGlowCyan)"
          />

          {/* 2. Risk Score Curve (Amber/Orange) */}
          <path
            d={riskPath}
            fill="none"
            stroke="#f59e0b"
            strokeWidth="2.4"
            filter="url(#lineGlowAmber)"
          />

          {/* 3. EAR Curve (Magenta/Purple) */}
          <path
            d={earPath}
            fill="none"
            stroke="#c084fc"
            strokeWidth="2.4"
            filter="url(#lineGlowPurple)"
          />

          {/* Highlight Key Dots on Curves */}
          {dotIndices.map((idx) => {
            const pt = dataPoints[idx];
            if (!pt) return null;
            const x = getX(idx);
            return (
              <g key={idx}>
                <circle cx={x} cy={getY(pt.hr)} r="3.5" fill="#38bdf8" stroke="#070b14" strokeWidth="1.5" />
                <circle cx={x} cy={getY(pt.risk)} r="3.5" fill="#f59e0b" stroke="#070b14" strokeWidth="1.5" />
                <circle cx={x} cy={getY(pt.ear)} r="3.5" fill="#c084fc" stroke="#070b14" strokeWidth="1.5" />
              </g>
            );
          })}

          {/* Interactive Hover Guides & Circles */}
          {dataPoints.map((pt, idx) => {
            const x = getX(idx);
            return (
              <rect
                key={idx}
                x={x - chartWidth / (dataPoints.length * 2)}
                y={paddingTop}
                width={chartWidth / dataPoints.length}
                height={chartHeight}
                fill="transparent"
                style={{ cursor: 'crosshair' }}
                onMouseEnter={() => setHoveredPoint({ ...pt, x })}
              />
            );
          })}

          {/* Hover Indicator Line & Floating Dot */}
          {hoveredPoint && (
            <g>
              <line
                x1={hoveredPoint.x}
                y1={paddingTop}
                x2={hoveredPoint.x}
                y2={paddingTop + chartHeight}
                stroke="rgba(255, 255, 255, 0.3)"
                strokeDasharray="2 2"
                strokeWidth="1"
              />
            </g>
          )}

          {/* X-axis Timestamps */}
          <g>
            <text x={paddingLeft} y={height - 8} fill="#94a3b8" fontSize="11" fontFamily="var(--font-mono)">
              {xLabels[0]}
            </text>
            <text x={paddingLeft + chartWidth * 0.33} y={height - 8} fill="#94a3b8" fontSize="11" fontFamily="var(--font-mono)" textAnchor="middle">
              {xLabels[1]}
            </text>
            <text x={paddingLeft + chartWidth * 0.66} y={height - 8} fill="#94a3b8" fontSize="11" fontFamily="var(--font-mono)" textAnchor="middle">
              {xLabels[2]}
            </text>
            <text x={width - paddingRight} y={height - 8} fill="#94a3b8" fontSize="11" fontFamily="var(--font-mono)" textAnchor="end">
              {xLabels[3]}
            </text>
          </g>
        </svg>

        {/* Hover Tooltip Popup */}
        {hoveredPoint && (
          <div style={{
            position: 'absolute',
            top: '8px',
            left: `${(hoveredPoint.x / width) * 100}%`,
            transform: 'translateX(-50%)',
            background: 'rgba(15, 23, 42, 0.95)',
            border: '1px solid rgba(255, 255, 255, 0.15)',
            borderRadius: '8px',
            padding: '0.45rem 0.75rem',
            fontSize: '0.75rem',
            color: '#f8fafc',
            boxShadow: '0 4px 14px rgba(0,0,0,0.5)',
            pointerEvents: 'none',
            zIndex: 10,
            whiteSpace: 'nowrap',
          }}>
            <div style={{ color: '#94a3b8', marginBottom: '0.2rem', fontFamily: 'var(--font-mono)' }}>
              🕒 {hoveredPoint.time}
            </div>
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <span style={{ color: '#f59e0b' }}>Risk: {hoveredPoint.risk}</span>
              <span style={{ color: '#38bdf8' }}>HR: {hoveredPoint.hr} BPM</span>
              <span style={{ color: '#c084fc' }}>EAR: {(hoveredPoint.ear / 100).toFixed(2)}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
