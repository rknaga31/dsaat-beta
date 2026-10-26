/**
 * API Client Service.
 * Centralized HTTP service for interacting with the FastAPI backend.
 */

const API_BASE_URL = import.meta.env?.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';

export async function fetchMonitoringStatus() {
  try {
    const response = await fetch(`${API_BASE_URL}/monitoring/status`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    // Return graceful offline fallback when backend is not running
    return {
      is_active: false,
      trip_duration_seconds: 0,
      risk_state: {
        timestamp: new Date().toISOString(),
        state: 'MONITORING_UNAVAILABLE',
        risk_score: 0,
        contributing_reasons: ['Backend service offline or unreachable at ' + API_BASE_URL],
        monitoring_reliable: false,
      },
      vision: null,
      sensor: null,
      gps: null,
      escalation: null,
      offline: true,
    };
  }
}

export async function startDriverSession(driverId = 'driver_default') {
  const response = await fetch(`${API_BASE_URL}/monitoring/session/start?driver_id=${encodeURIComponent(driverId)}`, {
    method: 'POST',
  });
  return await response.json();
}

export async function endDriverSession() {
  const response = await fetch(`${API_BASE_URL}/monitoring/session/end`, {
    method: 'POST',
  });
  return await response.json();
}

export async function triggerManualSos(reason = 'Driver manual dashboard emergency button') {
  const response = await fetch(`${API_BASE_URL}/alerts/sos?reason=${encodeURIComponent(reason)}`, {
    method: 'POST',
  });
  return await response.json();
}

export async function acknowledgeAlert() {
  const response = await fetch(`${API_BASE_URL}/alerts/acknowledge`, {
    method: 'POST',
  });
  return await response.json();
}

export async function fetchRecentAlerts(limit = 20) {
  try {
    const response = await fetch(`${API_BASE_URL}/alerts/recent?limit=${limit}`);
    if (!response.ok) return [];
    return await response.json();
  } catch (error) {
    return [];
  }
}

export async function sendVisionEvent(eventData) {
  try {
    const response = await fetch(`${API_BASE_URL}/monitoring/vision`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(eventData),
    });
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    return null;
  }
}

export async function sendSensorReading(readingData) {
  try {
    const response = await fetch(`${API_BASE_URL}/sensors/smartwatch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(readingData),
    });
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    return null;
  }
}

export async function sendGpsCoordinates(gpsData) {
  try {
    const response = await fetch(`${API_BASE_URL}/sensors/gps`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(gpsData),
    });
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    return null;
  }
}

export async function fetchNetworkInfo() {
  try {
    const response = await fetch(`${API_BASE_URL}/sensors/network-info`);
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    return null;
  }
}

export async function fetchSmartwatchVerification() {
  try {
    const response = await fetch(`${API_BASE_URL}/sensors/smartwatch/verify`);
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    return null;
  }
}

export async function updateEmergencyContact(phoneNumber, contactName = 'Primary Emergency Contact') {
  try {
    const response = await fetch(`${API_BASE_URL}/alerts/contact`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        phone_number: phoneNumber,
        contact_name: contactName,
      }),
    });
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    return null;
  }
}

export async function testBuzzer(level = 'WARNING') {
  try {
    const response = await fetch(`${API_BASE_URL}/alerts/test-beep?level=${encodeURIComponent(level)}`, {
      method: 'POST',
    });
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    return null;
  }
}
