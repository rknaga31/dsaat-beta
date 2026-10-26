"""
Sensors API Endpoints.
Receives physiological and geographical telemetry from smartwatch, Android GPS bridges,
and Google Health Connect / Google Fit integrations.
Provides local network address discovery and smartwatch verification procedures.
"""

import socket
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, Optional, List
from backend.schemas.sensor_schema import SensorReadingSchema
from backend.schemas.risk_schema import RiskStateSchema
from device_integration.android_gps.location_schema import GPSLocationSchema
from device_integration.smartwatch.boult_adapter import BoultSmartwatchAdapter
from backend.services.session_manager import session_manager
from backend.services.event_logger import event_logger
from backend.config.settings import get_settings
from shared.constants import (
    SensorDataStatusEnum,
    GpsFreshnessEnum,
    GpsPermissionEnum,
)

logger = logging.getLogger("sensors_api")
settings = get_settings()

router = APIRouter(prefix="/sensors", tags=["Device Sensors"])


def get_local_ip_addresses() -> List[str]:
    """Discovers LAN IP addresses of the host machine for Android phone connectivity."""
    ips: List[str] = []
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.1)
        s.connect(("8.8.8.8", 80))
        primary = s.getsockname()[0]
        s.close()
        if primary and not primary.startswith("127."):
            ips.append(primary)
    except Exception:
        pass

    try:
        hostname = socket.gethostname()
        for ip in socket.gethostbyname_ex(hostname)[2]:
            if not ip.startswith("127.") and ip not in ips:
                ips.append(ip)
    except Exception:
        pass

    if not ips:
        ips.append("127.0.0.1")
    return ips


@router.post(
    "/smartwatch",
    response_model=RiskStateSchema,
    summary="Ingest Smartwatch Biometric Telemetry",
    description="Accepts heart rate and sensor integrity packets from smartwatch adapter.",
)
async def ingest_sensor_reading(reading: SensorReadingSchema) -> RiskStateSchema:
    try:
        new_risk = session_manager.update_sensor(reading)
        return new_risk
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process sensor reading: {str(exc)}",
        )


@router.post(
    "/health_connect",
    response_model=RiskStateSchema,
    summary="Ingest Google Health Connect / Google Fit Telemetry",
    description="Accepts heart rate packets from Android Google Health Connect or Google Fit mobile webhooks.",
)
async def ingest_google_health(payload: Dict[str, Any]) -> RiskStateSchema:
    bpm_val = payload.get("heart_rate_bpm") or payload.get("bpm") or payload.get("value")
    if bpm_val is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing 'heart_rate_bpm' or 'bpm' in telemetry payload.",
        )

    try:
        bpm_float = float(bpm_val)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid heart rate value: {bpm_val}",
        )

    now_iso = datetime.now(timezone.utc).isoformat()
    source_name = str(payload.get("source", "google_health_connect"))
    data_status_str = str(payload.get("data_status", "CONNECTED_LIVE"))

    # Map status
    if data_status_str in ("CONNECTED_LIVE", "LIVE"):
        target_status = SensorDataStatusEnum.CONNECTED_LIVE
    elif data_status_str in ("CONNECTED_HISTORICAL", "HISTORICAL"):
        target_status = SensorDataStatusEnum.CONNECTED_HISTORICAL
    elif data_status_str in ("SIMULATED_DEMO", "SIMULATED"):
        target_status = SensorDataStatusEnum.SIMULATED_DEMO
    elif data_status_str in ("STALE_DATA", "STALE"):
        target_status = SensorDataStatusEnum.STALE_DATA
    else:
        target_status = SensorDataStatusEnum.CONNECTED_LIVE

    reading = SensorReadingSchema(
        timestamp=str(payload.get("timestamp", now_iso)),
        heart_rate_bpm=bpm_float,
        source=source_name,
        data_status=target_status,
        last_reading_timestamp=now_iso,
        device_battery_percent=float(payload.get("battery_percent")) if payload.get("battery_percent") is not None else None,
        connection_status=True,
        data_freshness_seconds=0.0,
    )
    return session_manager.update_sensor(reading)


@router.get(
    "/status",
    summary="Get Latest Sensor Reading",
    description="Returns the most recent biometric telemetry sample received.",
)
async def get_sensor_status() -> Dict[str, Any]:
    latest = session_manager.latest_sensor_reading
    if not latest:
        return {
            "status": "UNAVAILABLE",
            "message": "No sensor packets received yet",
            "data": None,
        }
    return {
        "status": latest.data_status,
        "data": latest.model_dump(),
    }


@router.get(
    "/smartwatch/verify",
    summary="Audit Smartwatch Hardware Compatibility",
    description="Returns vendor compatibility assessment and documented verification checklist.",
)
async def verify_smartwatch_compatibility() -> Dict[str, Any]:
    return BoultSmartwatchAdapter.verify_device_compatibility(mac_address=settings.BOULT_MAC_ADDRESS)


@router.post(
    "/gps",
    summary="Ingest GPS Location Telemetry",
    description="Receives geographical coordinates from Android GPS bridge or mobile browser.",
)
async def ingest_gps_coordinates(payload: Dict[str, Any]) -> Dict[str, Any]:
    now_iso = datetime.now(timezone.utc).isoformat()

    lat = payload.get("latitude")
    lon = payload.get("longitude")
    source = str(payload.get("source", "android_gps_bridge"))
    perm_status_str = str(payload.get("permission_status", "GRANTED"))
    accuracy = float(payload.get("accuracy_m")) if payload.get("accuracy_m") is not None else None
    speed = float(payload.get("speed_kmh")) if payload.get("speed_kmh") is not None else None
    error_state = payload.get("error_state")

    perm_status = GpsPermissionEnum.GRANTED
    if perm_status_str.upper() == "DENIED":
        perm_status = GpsPermissionEnum.DENIED
    elif perm_status_str.upper() == "UNAVAILABLE":
        perm_status = GpsPermissionEnum.UNAVAILABLE

    if lat is not None and lon is not None:
        loc = GPSLocationSchema(
            timestamp=str(payload.get("timestamp", now_iso)),
            latitude=float(lat),
            longitude=float(lon),
            accuracy_m=accuracy,
            speed_kmh=speed,
            source=source,
            permission_status=perm_status,
            freshness_status=GpsFreshnessEnum.LIVE,
            is_valid=True,
            error_state=error_state,
        )
    else:
        loc = GPSLocationSchema(
            timestamp=str(payload.get("timestamp", now_iso)),
            latitude=None,
            longitude=None,
            source=source,
            permission_status=perm_status,
            freshness_status=GpsFreshnessEnum.UNAVAILABLE,
            is_valid=False,
            error_state=error_state or "GPS coordinates unavailable or permission denied.",
        )

    record = session_manager.update_gps_location(loc)
    return {"status": "ACKNOWLEDGED", "gps": record}


@router.get(
    "/gps",
    summary="Get Current GPS Location",
    description="Returns the latest verified vehicle location and freshness status.",
)
async def get_current_gps() -> Dict[str, Any]:
    status_packet = session_manager.get_current_status()
    return status_packet.get("gps") or {
        "latitude": None,
        "longitude": None,
        "permission_status": "NOT_REQUESTED",
        "freshness_status": "UNAVAILABLE",
        "is_valid": False,
    }


@router.get(
    "/network-info",
    summary="Get Host Network Addresses & Bridge URLs",
    description="Returns local IP addresses and mobile connection URLs for Android GPS and Health Connect bridges.",
)
async def get_network_info() -> Dict[str, Any]:
    ips = get_local_ip_addresses()
    port = settings.BACKEND_PORT
    frontend_port = 5173

    primary_ip = ips[0]
    return {
        "host_ips": ips,
        "primary_ip": primary_ip,
        "backend_port": port,
        "frontend_port": frontend_port,
        "gps_webhook_url": f"http://{primary_ip}:{port}/api/v1/sensors/gps",
        "health_connect_webhook_url": f"http://{primary_ip}:{port}/api/v1/sensors/health_connect",
        "mobile_dashboard_url": f"http://{primary_ip}:{frontend_port}",
        "https_requirement_note": (
            "Modern Android browsers require a Secure Context (HTTPS or localhost) for navigator.geolocation. "
            "For LAN access, either use an Android Webhook app (GPS Logger/Automate) posting to the gps_webhook_url, "
            "or use USB reverse tethering ('adb reverse tcp:5173 tcp:5173') to open http://localhost:5173 on the phone."
        ),
    }
