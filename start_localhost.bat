@echo off
TITLE D-SAAT Localhost Launcher
echo =======================================================
echo    D-SAAT: Multimodal Driver Safety Telemetry
echo    Starting Localhost Development Servers
echo =======================================================
echo.
echo [1/2] Starting FastAPI Backend on http://localhost:8000/docs ...
start "D-SAAT Backend (Port 8000)" cmd /k "python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

echo [2/2] Starting Vite Frontend Cockpit on http://localhost:5173/ ...
cd frontend
start "D-SAAT Frontend (Port 5173)" cmd /k "call npm.cmd run dev"
cd ..

echo.
echo Both servers have been launched in separate terminal windows!
echo Backend Docs:  http://localhost:8000/docs
echo Web Cockpit:   http://localhost:5173/
echo.
ping 127.0.0.1 -n 4 >nul
start http://localhost:5173/
