import React from 'react';

function getEventBadge(eventType) {
  switch (eventType) {
    case 'alert_dispatched':
      return <span className="badge badge-danger">ALERT DISPATCHED</span>;
    case 'risk_escalation':
      return <span className="badge badge-warning">RISK ESCALATION</span>;
    case 'session_started':
      return <span className="badge badge-normal">SESSION START</span>;
    case 'session_ended':
      return <span className="badge badge-muted">SESSION END</span>;
    case 'sensor_reading':
      return <span className="badge badge-info">BIOMETRIC</span>;
    case 'gps_reading':
      return <span className="badge badge-info">GPS UPDATE</span>;
    default:
      return <span className="badge badge-muted">{eventType?.replace(/_/g, ' ')}</span>;
  }
}

function formatEventDetails(data, eventType) {
  if (!data) return '--';
  if (typeof data !== 'object') return String(data);

  if (eventType === 'risk_escalation') {
    const score = data.score !== undefined ? `Risk Score: ${data.score}` : '';
    const reasons = Array.isArray(data.reasons) ? data.reasons.join(', ') : '';
    return [score, reasons].filter(Boolean).join(' • ');
  }

  if (eventType === 'alert_dispatched') {
    const alertId = data.alert_id ? `ID: ${data.alert_id.slice(0, 8)}` : '';
    const contact = data.contact ? `Contact: ${data.contact}` : '';
    return [alertId, contact].filter(Boolean).join(' • ') || 'Emergency alert dispatched';
  }

  if (eventType === 'sensor_reading') {
    const bpm = data.heart_rate_bpm ? `${Math.round(data.heart_rate_bpm)} BPM` : 'No BPM';
    const status = data.connection_status || '';
    return [bpm, status].filter(Boolean).join(' • ');
  }

  // General clean JSON view
  try {
    const keys = Object.keys(data).filter(k => k !== 'timestamp');
    return keys.slice(0, 3).map(k => `${k}: ${JSON.stringify(data[k])}`).join(' • ');
  } catch {
    return JSON.stringify(data).slice(0, 80);
  }
}

export function EventHistory({ events }) {
  const formatTime = (isoString) => {
    if (!isoString) return '--';
    try {
      const d = new Date(isoString);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
      return isoString;
    }
  };

  return (
    <div className="glass-panel">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontSize: '1.1rem' }}>📋</span>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc', letterSpacing: '-0.01em' }}>
            Event & Alert Audit Log
          </h3>
        </div>
        <span style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>
          Latest {events.length} records
        </span>
      </div>

      {events.length === 0 ? (
        <div style={{
          textAlign: 'center',
          padding: '2rem 1rem',
          color: '#64748b',
          fontSize: '0.85rem',
          background: 'rgba(2, 6, 23, 0.4)',
          borderRadius: '10px',
          border: '1px dashed rgba(255,255,255,0.08)',
        }}>
          No telemetry or alert events recorded in this active session yet.
        </div>
      ) : (
        <div style={{ maxHeight: '220px', overflowY: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
            <thead>
              <tr style={{
                borderBottom: '1px solid rgba(255,255,255,0.08)',
                color: '#94a3b8',
                textAlign: 'left',
                fontSize: '0.72rem',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
              }}>
                <th style={{ padding: '0.5rem 0.75rem', width: '110px' }}>Timestamp</th>
                <th style={{ padding: '0.5rem 0.75rem', width: '160px' }}>Event Classification</th>
                <th style={{ padding: '0.5rem 0.75rem' }}>Context / Telemetry Detail</th>
              </tr>
            </thead>
            <tbody>
              {events.map((e, idx) => (
                <tr key={idx} style={{
                  borderBottom: '1px solid rgba(255,255,255,0.04)',
                  transition: 'background-color 0.15s ease',
                }}>
                  <td style={{
                    padding: '0.6rem 0.75rem',
                    color: '#94a3b8',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.78rem',
                  }}>
                    {formatTime(e.timestamp)}
                  </td>
                  <td style={{ padding: '0.6rem 0.75rem' }}>
                    {getEventBadge(e.event_type)}
                  </td>
                  <td style={{
                    padding: '0.6rem 0.75rem',
                    color: '#cbd5e1',
                    fontSize: '0.8rem',
                    wordBreak: 'break-word',
                  }}>
                    {formatEventDetails(e.data, e.event_type)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
