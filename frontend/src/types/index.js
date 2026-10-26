/**
 * Frontend Type Definitions & Enum Constants.
 * Mirrors shared system contracts from backend and shared/constants.py.
 */

export const RiskState = {
  NORMAL: 'NORMAL',
  WARNING: 'WARNING',
  HIGH_RISK: 'HIGH_RISK',
  MONITORING_UNAVAILABLE: 'MONITORING_UNAVAILABLE',
};

export const EyeStatus = {
  OPEN: 'OPEN',
  CLOSED: 'CLOSED',
  PARTIAL: 'PARTIAL',
  UNKNOWN: 'UNKNOWN',
};

export const SensorDataStatus = {
  CONNECTED_LIVE: 'CONNECTED_LIVE',
  CONNECTED_HISTORICAL: 'CONNECTED_HISTORICAL',
  SIMULATED_DEMO: 'SIMULATED_DEMO',
  UNAVAILABLE: 'UNAVAILABLE',
  STALE_DATA: 'STALE_DATA',
  // Backward compatibility
  LIVE: 'CONNECTED_LIVE',
  SIMULATED: 'SIMULATED_DEMO',
  STALE: 'STALE_DATA',
};

export const GpsFreshness = {
  LIVE: 'LIVE',
  STALE: 'STALE',
  UNAVAILABLE: 'UNAVAILABLE',
  SIMULATED: 'SIMULATED',
};

export const GpsPermission = {
  GRANTED: 'GRANTED',
  DENIED: 'DENIED',
  PROMPT: 'PROMPT',
  UNAVAILABLE: 'UNAVAILABLE',
  NOT_REQUESTED: 'NOT_REQUESTED',
};

export const EscalationStage = {
  NORMAL: 'NORMAL',
  WARNING: 'WARNING',
  HIGH_RISK: 'HIGH_RISK',
  ESCALATION_PENDING: 'ESCALATION_PENDING',
  FAMILY_SMS: 'FAMILY_SMS',
};

export const AlertLevel = {
  INFO: 'INFO',
  WARNING: 'WARNING',
  CRITICAL: 'CRITICAL',
};

export const SmsStatus = {
  NOT_TRIGGERED: 'NOT_TRIGGERED',
  ESCALATION_PENDING: 'ESCALATION_PENDING',
  QUEUED: 'QUEUED',
  SUBMITTED: 'SUBMITTED',
  SENT: 'SENT',
  DELIVERED: 'DELIVERED',
  MOCK_SENT: 'MOCK_SENT',
  FAILED: 'FAILED',
};
