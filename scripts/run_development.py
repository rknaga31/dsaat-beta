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
    print("\n--- Launching FastAPI Backend on http://127.0.0.1:8000 ---")
    try:
        subprocess.run(
            [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"],
            cwd=str(PROJECT_ROOT),
        )
    except KeyboardInterrupt:
        print("\nBackend stopped.")


def run_tests():
    print("\n--- Running Pytest Suite Across All Modules ---")
    subprocess.run([sys.executable, "-m", "pytest", "-v"], cwd=str(PROJECT_ROOT))


def run_check():
    print("\n--- Running System Integrity Setup Check ---")
    subprocess.run([sys.executable, "scripts/setup_check.py"], cwd=str(PROJECT_ROOT))


def main():
    if len(sys.argv) < 2:
        print("\nUsage: python scripts/run_development.py [backend | test | check]")
        print("  backend : Starts the FastAPI backend with hot-reload")
        print("  test    : Runs the unit test suite across all 5 modules")
        print("  check   : Runs the system structure and schema verification check")
        sys.exit(0)

    cmd = sys.argv[1].lower()
    if cmd == "backend":
        launch_backend()
    elif cmd == "test":
        run_tests()
    elif cmd == "check":
        run_check()
    else:
        print(f"Unknown command '{cmd}'. Available: backend, test, check")


if __name__ == "__main__":
    main()
