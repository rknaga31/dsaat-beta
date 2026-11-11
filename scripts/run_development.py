"""
Development Launcher Script.
Provides unified commands to launch the FastAPI backend, simulate sensor feeds,
or run verification tests.
"""

import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def launch_backend():
    print("\n--- Launching FastAPI Backend on http://localhost:8000 ---")
    try:
        subprocess.run(
            [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
            cwd=str(PROJECT_ROOT),
        )
    except KeyboardInterrupt:
        print("\nBackend stopped.")


def launch_frontend():
    print("\n--- Launching Vite Frontend on http://localhost:5173 ---")
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    frontend_dir = PROJECT_ROOT / "frontend"
    try:
        subprocess.run([npm_cmd, "run", "dev"], cwd=str(frontend_dir))
    except KeyboardInterrupt:
        print("\nFrontend stopped.")


def launch_all():
    print("\n=======================================================")
    print("  Starting D-SAAT Full Stack (Backend + Frontend)")
    print("  Backend API:  http://localhost:8000/docs")
    print("  Web Cockpit:  http://localhost:5173/")
    print("=======================================================\n")
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    frontend_dir = PROJECT_ROOT / "frontend"

    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
        cwd=str(PROJECT_ROOT),
    )

    try:
        subprocess.run([npm_cmd, "run", "dev"], cwd=str(frontend_dir))
    except KeyboardInterrupt:
        pass
    finally:
        print("\nShutting down backend...")
        backend_proc.terminate()
        backend_proc.wait()


def run_tests():
    print("\n--- Running Pytest Suite Across All Modules ---")
    subprocess.run([sys.executable, "-m", "pytest", "-v"], cwd=str(PROJECT_ROOT))


def run_check():
    print("\n--- Running System Integrity Setup Check ---")
    subprocess.run([sys.executable, "scripts/setup_check.py"], cwd=str(PROJECT_ROOT))


def main():
    if len(sys.argv) < 2:
        print("\nUsage: python scripts/run_development.py [all | backend | frontend | test | check]")
        print("  all      : Starts both FastAPI backend AND Vite frontend simultaneously")
        print("  backend  : Starts only the FastAPI backend on port 8000")
        print("  frontend : Starts only the Vite frontend on port 5173")
        print("  test     : Runs the unit test suite across all 5 modules")
        print("  check    : Runs the system structure and schema verification check")
        sys.exit(0)

    cmd = sys.argv[1].lower()
    if cmd == "all":
        launch_all()
    elif cmd == "backend":
        launch_backend()
    elif cmd == "frontend":
        launch_frontend()
    elif cmd == "test":
        run_tests()
    elif cmd == "check":
        run_check()
    else:
        print(f"Unknown command '{cmd}'. Available: all, backend, frontend, test, check")


if __name__ == "__main__":
    main()
