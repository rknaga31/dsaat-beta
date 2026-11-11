# 📍 100% Free GPS Location Detection & Emergency Alert Blueprint

> **Zero-Cost Architecture**: Every feature described in this guide is **100% free of cost**, requires **zero paid subscriptions**, **zero paid APIs**, and **no credit card**.

---

## 📌 Table of Contents
1. [Core Architecture Status: Smartwatch as Future Hardware Enhancement](#1-core-architecture-status-smartwatch-as-future-hardware-enhancement)
2. [100% Free GPS Location Detection](#2-100-free-gps-location-detection)
3. [100% Free Emergency Alert Dispatch](#3-100-free-emergency-alert-dispatch)
   - [Option A: Free Email Alerts via Gmail SMTP](#option-a-free-email-alerts-via-gmail-smtp)
   - [Option B: Free Instant Messages via Telegram Bot](#option-b-free-instant-messages-via-telegram-bot)
4. [In-Cabin Free Audio Alarm Engine](#4-in-cabin-free-audio-alarm-engine)
5. [Summary of Zero-Cost Configurations](#5-summary-of-zero-cost-configurations)

---

## 1. Core Architecture Status: Smartwatch as Future Hardware Enhancement

In D-SAAT, multimodal fusion is the foundational innovation:
* **The Core Idea**: Combining **Computer Vision (Eyes/Mouth/Head)** + **GPS (Speed/Location)** + **Physiological Biometrics (Heart Rate/HRV)**.
* **Phase 1 (Current Stage)**:
  * The system is **fully functional standalone** using **AI Camera Vision + Real GPS Location + Cabin Audio Buzzer + Free Emergency Notifications**.
  * The **Risk Engine mathematically fuses biometrics**, and the **Biometric Simulator Strip** in the Cockpit allows demonstrating normal, drowsy (bradycardia), panic (tachycardia), and stale states with one click.
  * **Safe Hardware Decoupling**: If no physical watch is connected, the system gracefully operates on camera and GPS telemetry without failing or fabricating readings.
* **Phase 2 (Future Hardware Roadmap)**:
  * Pairing physical commercial smartwatches (e.g. boAt Storm Infinity, Boult Drift, Noise) via dedicated Android Bluetooth background daemons or direct BLE GATT `0x180D`.

---

## 2. 100% Free GPS Location Detection

You do **NOT** need any paid Google Maps API keys or third-party paid geolocation services to acquire live GPS.

### Method 1: Built-in Browser Geolocation (One-Click, Zero-Setup)
* **Technology**: W3C Standard `navigator.geolocation.watchPosition` (integrated in `frontend/src/components/SensorCard.jsx`).
* **Cost**: **$0.00** (Native browser API).
* **How It Works**:
  1. Open the D-SAAT dashboard at `http://localhost:5173/`.
  2. Under the **Android Phone GPS Bridge** card, click **"📡 Acquire Browser GPS"**.
  3. Click **"Allow"** when your browser asks for location permission.
  4. Your laptop/phone retrieves high-accuracy latitude, longitude, and ground speed in real time and streams it to `/api/v1/sensors/gps`.

### Method 2: Free Open-Source Android GPS Webhook (For In-Car Use)
* **Technology**: **GPS Logger for Android** (Free & Open-Source on F-Droid / GitHub / Play Store) or **MacroDroid**.
* **Cost**: **$0.00**.
* **How It Works**:
  1. Install *GPS Logger for Android*.
  2. In Settings → *Log to Custom URL*, set:
     ```text
     http://<LAPTOP_IP>:8000/api/v1/sensors/gps
     ```
  3. HTTP Method: `POST` with JSON body:
     ```json
     {
       "latitude": %LAT,
       "longitude": %LON,
       "speed_kmh": %SPD,
       "source": "android_gps_logger"
     }
     ```
  4. The phone's hardware satellite GPS chip streams accurate highway speed and coordinates directly over Wi-Fi.

### Zero-Cost Google Maps Pin Generation
When an emergency occurs, D-SAAT generates a standard, interactive Google Maps link:
```text
https://maps.google.com/?q={latitude},{longitude}
```
* **Cost**: **$0.00** (Standard URL schema; does NOT require a Google Maps Platform developer account or billing).

---

## 3. 100% Free Emergency Alert Dispatch

Instead of paid cellular SMS APIs (like Twilio which requires balance/credit card), D-SAAT includes **two 100% free notification backends**:

---

### Option A: Free Email Alerts via Gmail SMTP
Uses Python's built-in standard library (`smtplib` + `email.mime`). Works with any standard email account (Gmail, Outlook, Yahoo) with **zero subscription fees**.

#### 2-Minute Setup:
1. Go to your Google Account security page: [https://myaccount.google.com/security](https://myaccount.google.com/security)
2. Ensure **2-Step Verification** is turned ON.
3. Search for **"App Passwords"** (or go to [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)).
4. Create a new App Password named **"D-SAAT Alert System"**. Google will generate a 16-character code (e.g., `abcd efgh ijkl mnop`).
5. Open your `.env` file in the project folder and configure:
   ```env
   # Set provider to email
   SMS_PROVIDER=email

   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your_email@gmail.com
   SMTP_PASSWORD=abcdefghijklmnop
   EMERGENCY_CONTACT_EMAIL=family_member@gmail.com
   ```
6. **Done!** Whenever critical fatigue or micro-sleep is detected (Stage 4), an urgent, HTML-styled emergency alert is instantly delivered to the family's inbox with the live Google Maps pin!

---

### Option B: Free Instant Messages via Telegram Bot
Delivers instant push notifications with alert sounds directly to family members' Android/iOS smartphones. Completely free forever.

#### 1-Minute Setup:
1. Open Telegram and search for **`@BotFather`**.
2. Send `/newbot`, choose a name and username (e.g. `MyDSAATAlertBot`).
3. BotFather gives you an HTTP API token (e.g. `7123456789:ABCdefGHIjklMNOpqrSTUvwxYZ`).
4. Search for **`@userinfobot`** in Telegram to find your numeric **Chat ID** (e.g. `987654321`).
5. Open your `.env` file and configure:
   ```env
   SMS_PROVIDER=telegram

   TELEGRAM_BOT_TOKEN=7123456789:ABCdefGHIjklMNOpqrSTUvwxYZ
   TELEGRAM_CHAT_ID=987654321
   ```
6. **Done!** Instant phone notifications arrive in real time with zero network charges!

---

## 4. In-Cabin Free Audio Alarm Engine

D-SAAT uses browser **Web Audio API** and Python `winsound` / daemon buzzers:
* **800 Hz Chime**: Warning stage (frequent yawning).
* **1500 Hz - 2500 Hz High-Pitch Pulsing Siren**: Stage 2 & 3 critical micro-sleep alarm to physically wake the driver.
* **10-Second Countdown Window**: Driver can tap **"I Am Awake"** on the screen to silence the alarm and abort the emergency dispatch.
* **Cost**: **$0.00** (Local sound hardware).

---

## 5. Summary of Zero-Cost Configurations

| Component | Technology | Setup Cost | Running Cost | API Key / Account Required? |
| :--- | :--- | :--- | :--- | :--- |
| **Facial AI Tracking** | MediaPipe FaceMesh (Client-side WebAssembly) | $0.00 | $0.00 | No (Runs locally in browser) |
| **GPS Location Tracking** | W3C Browser Geolocation / Android GPS Webhook | $0.00 | $0.00 | No (Uses device GPS hardware) |
| **Google Maps Pin** | Standard Google Maps Query URL | $0.00 | $0.00 | No |
| **In-Cabin Siren** | Web Audio API / Local Speakers | $0.00 | $0.00 | No |
| **Family Alert via Email** | Python `smtplib` + Gmail App Password | $0.00 | $0.00 | Free Gmail account |
| **Family Alert via Telegram** | Telegram Bot API | $0.00 | $0.00 | Free Telegram account |
| **Biometric Telemetry** | Simulated Vitals / Core Roadmap Architecture | $0.00 | $0.00 | No |
