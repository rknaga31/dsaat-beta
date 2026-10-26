# Team Developer Setup Guide

This guide walks every team member through configuring their local workstation.

---

## 1. Prerequisites

* **Python**: 3.10 or newer (tested on Python 3.13)
* **Node.js**: 18.0 or newer (with npm)
* **Webcam**: Required for Member 2 (AI Vision); simulated frames can be used for others.

---

## 2. Step-by-Step Installation

### Step 1: Clone & Configure Environment
In the repository root, copy the environment template:

```bash
# Windows (PowerShell)
Copy-Item .env.example .env

# Linux / macOS
cp .env.example .env
```

Review `.env` to customize settings. By default, `SMS_PROVIDER=mock` and `SMARTWATCH_SOURCE=SIMULATED` to avoid external costs.

---

### Step 2: Set Up Python Virtual Environment
Create and activate an isolated virtual environment:

```bash
# Create virtual environment
python -m venv .venv

# Activate on Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Activate on Linux / macOS
source .venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip

# Install root dependencies
pip install -r requirements.txt
```

Member 2 (AI Vision) should also install vision requirements:
```bash
pip install -r ai_vision/requirements.txt
```

---

### Step 3: Set Up Frontend Dashboard
Install Node dependencies:

```bash
cd frontend
npm install
cd ..
```

---

### Step 4: Run Automated Verification Check
Execute the setup check script to verify Python versions, JSON schema validity, package imports, and directory integrity:

```bash
python scripts/setup_check.py
```

---

### Step 5: Launching the Development Stack

1. **Terminal 1: Start Backend API**:
   ```bash
   python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
   ```

2. **Terminal 2: Start Frontend Dashboard**:
   ```bash
   cd frontend
   npm run dev
   ```

3. **Terminal 3: Start AI Vision Capture** (Optional for Member 2):
   ```bash
   python -c "from ai_vision.vision_service import VisionService; v = VisionService(); print('Vision service ready')"
   ```
