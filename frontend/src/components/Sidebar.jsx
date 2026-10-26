import React from 'react';

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Dashboard', icon: '🏠' },
  { id: 'video', label: 'Live Video', icon: '📹' },
  { id: 'health', label: 'Health Data', icon: '🩺' },
  { id: 'history', label: 'Trip History', icon: '🔄' },
  { id: 'alerts', label: 'Alerts', icon: '🔔' },
  { id: 'settings', label: 'Settings', icon: '⚙️' },
];

export function Sidebar({ activeTab, onSelectTab }) {
  return (
    <aside style={{
      width: '210px',
      flexShrink: 0,
      display: 'flex',
      flexDirection: 'column',
      gap: '0.4rem',
      padding: '0.5rem 0',
    }}>
      {NAV_ITEMS.map((item) => {
        const isActive = activeTab === item.id;
        return (
          <button
            key={item.id}
            onClick={() => onSelectTab(item.id)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.85rem',
              padding: '0.8rem 1.1rem',
              borderRadius: '12px',
              border: 'none',
              cursor: 'pointer',
              fontFamily: 'var(--font-family)',
              fontSize: '0.92rem',
              fontWeight: isActive ? 700 : 500,
              color: isActive ? '#f8fafc' : '#94a3b8',
              background: isActive
                ? 'linear-gradient(90deg, rgba(37, 99, 235, 0.45) 0%, rgba(14, 116, 144, 0.25) 100%)'
                : 'transparent',
              position: 'relative',
              textAlign: 'left',
              transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
              boxShadow: isActive ? '0 4px 20px rgba(37, 99, 235, 0.25)' : 'none',
              borderLeft: isActive ? '3px solid #38bdf8' : '3px solid transparent',
            }}
            onMouseEnter={(e) => {
              if (!isActive) {
                e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)';
                e.currentTarget.style.color = '#e2e8f0';
              }
            }}
            onMouseLeave={(e) => {
              if (!isActive) {
                e.currentTarget.style.background = 'transparent';
                e.currentTarget.style.color = '#94a3b8';
              }
            }}
          >
            <span style={{
              fontSize: '1.15rem',
              filter: isActive ? 'drop-shadow(0 0 8px rgba(56, 189, 248, 0.8))' : 'none',
            }}>
              {item.icon}
            </span>
            <span>{item.label}</span>
          </button>
        );
      })}
    </aside>
  );
}
