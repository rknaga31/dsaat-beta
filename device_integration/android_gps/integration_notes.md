# Android GPS to Laptop Integration Notes

**Author:** Member 4 — Smartwatch & GPS Integration Engineer

---

## 1. Problem Statement & Technical Reality

Laptops do not possess internal GNSS/GPS satellite receivers. A laptop running the driver monitoring system cannot magically query the driver's phone location over the air without an explicit network or hardware transport bridge.

Therefore, Member 4 is tasked with implementing a tested bridge between the Android smartphone and the backend laptop.

---

## 2. Tested Integration Architectures

### Option A: Local Wi-Fi HTTP POST Webhook (Recommended for Semester Demo)
* **How it works**: Both the laptop and Android phone connect to the same Wi-Fi network (or the phone's mobile hotspot).
* **On Android**: An open-source GPS client (such as *GPS Logger for Android*, *MacroDroid*, or *Automate*) is configured to send periodic HTTP POST packets to `http://<LAPTOP_LOCAL_IP>:8000/api/v1/sensors/gps`.
* **Payload**:
  ```json
  {
    "timestamp": "2026-10-26T12:00:00.000Z",
    "latitude": 12.9716,
    "longitude": 77.5946,
    "speed_kmh": 40.0,
    "accuracy_m": 5.0,
    "source": "android_http_webhook"
  }
  ```
* **Pros**: Simple, highly reliable, no proprietary APK compile needed.

---

### Option B: Termux CLI Bridge (For Advanced Testing)
* **On Android**: Install Termux and Termux:API.
* **Command**: Run a bash loop emitting location every 2 seconds:
  ```bash
  while true; do
    LOC=$(termux-location -p gps)
    curl -X POST http://<LAPTOP_IP>:8000/api/v1/sensors/gps -H "Content-Type: application/json" -d "$LOC"
    sleep 2
  done
  ```

---

### Option C: Mobile Web Browser Geolocation
* The driver or copilot opens the frontend dashboard URL in Chrome on their Android phone (`http://<LAPTOP_IP>:5173`).
* The browser requests standard HTML5 `navigator.geolocation.watchPosition()`.
* Coordinates are forwarded via WebSocket or REST to the backend.

---

### Option D: Simulated GPS Fallback
* When running without an active phone bridge, the system loads `DEFAULT_LATITUDE` and `DEFAULT_LONGITUDE` from `.env` and flags `source="simulated_gps"`.
