# Smartwatch & Google Health Connect Integration Guide

This guide explains how to connect consumer smartwatches (Boult, Boat, Noise, Samsung Galaxy Watch, Fitbit) and the **Google Health Connect** app to the Driver Drowsiness and Health Monitoring System.

---

## 1. Is Google Health App Good for this Project?

**Yes, absolutely.** Google Health Connect is the modern Android standard for centralized health telemetry.

### How It Works in Practice
Consumer smartwatches from brands like **Boult**, **Boat**, **Noise**, or **Samsung** do not have built-in Wi-Fi or cellular connections to speak directly to your laptop. Instead, they pair via Bluetooth to their official companion apps on your Android phone (e.g., *Boult Fit*, *Da Fit*, *FitCloudPro*, *Samsung Health*, *Fitbit*).

```text
+-----------------------+
|  Physical Smartwatch  | (Boult, Boat, Noise, Galaxy Watch)
+-----------+-----------+
            | (Bluetooth LE / Sync)
            v
+-----------------------+
| Mobile Companion App  | (Boult Fit, Da Fit, Samsung Health)
+-----------+-----------+
            | (Android Health Permissions)
            v
+-----------------------+
| Google Health Connect | (Centralized Android Health Store)
+-----------+-----------+
            | (Local Wi-Fi HTTP POST Webhook)
            v
+-----------------------+
| FastAPI Backend Server| (http://<laptop-ip>:8000/api/v1/sensors/health_connect)
+-----------------------+
```

---

## 2. Step-by-Step Setup: Connecting Your Android Phone & Watch

### Step 1: Sync Your Watch with Google Health Connect
1. On your Android phone, install **Google Health Connect** (built into Android 14 settings under `Settings > Security & Privacy > Health Connect`, or available on Google Play for Android 9+).
2. Open your watch's companion app (e.g. *Boult Fit*, *Da Fit*, or *Samsung Health*).
3. Under **Settings > Connected Apps / Data Sharing**, enable **Google Health Connect** or **Google Fit**.
4. *(Tip for Boult/Boat watches)*: If your specific companion app lacks direct Health Connect export, install the popular free app **Health Sync** from Google Play. Select your watch companion app as the source and Google Health Connect as the destination.

---

### Step 2: Bridge Data from Android to the Laptop Backend

Your laptop and Android phone must be on the same local Wi-Fi network (or connected to your phone's Wi-Fi hotspot).

Find your laptop's local IP address (e.g. `192.168.1.15`):
* On Windows, run `ipconfig` in PowerShell and look for `IPv4 Address`.

Your backend webhook endpoint is:
```text
http://<YOUR_LAPTOP_IP>:8000/api/v1/sensors/health_connect
```

#### Method A: Using an Android Webhook App (Automate / MacroDroid / Tasker)
1. Install **MacroDroid** or **Automate** (free on Google Play).
2. Create a trigger: **Every 3 seconds** (or on Heart Rate update).
3. Create an action: **HTTP Request (POST)**:
   - **URL**: `http://192.168.1.15:8000/api/v1/sensors/health_connect`
   - **Method**: `POST`
   - **Content-Type**: `application/json`
   - **Body**:
     ```json
     {
       "heart_rate_bpm": 74.0,
       "source": "google_health_connect",
       "battery_percent": 85.0
     }
     ```
4. Save and enable the macro. Whenever your watch records heart rate, it is pushed directly to the dashboard in real time!

---

### Step 3: Testing from the Web Dashboard (Zero-Hardware Simulator)

In [`frontend/src/components/SensorCard.jsx`](file:///c:/Users/rnaga/.antigravity-ide/d-saat/frontend/src/components/SensorCard.jsx), we have integrated an interactive **Live Physiological Injection Bar**:

1. Open `http://127.0.0.1:5173/` in your browser.
2. Under the **Biometrics & Device Status** card, click:
   - **💚 Normal (74 BPM)**: Verifies steady alert resting heart rate.
   - **⚠️ Drowsy (48 BPM)**: Injects bradycardia to test drowsiness risk escalation.
   - **🚨 Panic (122 BPM)**: Injects elevated stress distress.
   - **❌ Disconnect**: Verifies that missing readings are cleanly handled as `UNAVAILABLE` without corrupting the score.
3. Click **"🔗 Google Health Setup"** to view and copy your dynamic local webhook URL.
