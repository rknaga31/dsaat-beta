import { useState, useEffect, useCallback } from 'react';
import {
  fetchMonitoringStatus,
  fetchRecentAlerts,
  startDriverSession,
  endDriverSession,
  triggerManualSos,
  acknowledgeAlert,
} from '../services/apiClient';

export function useMonitoring(pollIntervalMs = 1500) {
  const [statusData, setStatusData] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isBackendOffline, setIsBackendOffline] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const data = await fetchMonitoringStatus();
      setStatusData(data);
      setIsBackendOffline(Boolean(data?.offline));

      const alertList = await fetchRecentAlerts(15);
      setAlerts(alertList);
    } catch (err) {
      console.error('Monitoring poll error:', err);
      setIsBackendOffline(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, pollIntervalMs);
    return () => clearInterval(interval);
  }, [refresh, pollIntervalMs]);

  const handleStartSession = async (driverId) => {
    await startDriverSession(driverId);
    await refresh();
  };

  const handleEndSession = async () => {
    await endDriverSession();
    await refresh();
  };

  const handleTriggerSos = async () => {
    await triggerManualSos();
    await refresh();
  };

  const handleAcknowledge = async () => {
    await acknowledgeAlert();
    await refresh();
  };

  return {
    statusData,
    alerts,
    loading,
    isBackendOffline,
    startSession: handleStartSession,
    endSession: handleEndSession,
    triggerSos: handleTriggerSos,
    acknowledge: handleAcknowledge,
    refresh,
  };
}
