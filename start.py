#!/usr/bin/env python3
"""
PAFRL React+Python Demo — One-Click Startup
Launches the Flask backend and Vite dev server together.

Usage:  python start.py
Then open: http://localhost:5173
"""
import subprocess, sys, os, time, webbrowser, threading, shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "backend")
FRONTEND = os.path.join(ROOT, "frontend")


def check_python_deps():
    missing = []
    for pkg in ["flask", "numpy", "sklearn"]:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"Installing missing Python packages: {missing}")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "flask", "numpy", "scikit-learn", "--break-system-packages", "-q"
        ])


def check_node():
    if shutil.which("npm") is None:
        print("\nERROR: npm not found. Please install Node.js (https://nodejs.org) first.\n")
        sys.exit(1)


def install_frontend_deps():
    if not os.path.exists(os.path.join(FRONTEND, "node_modules")):
        print("Installing frontend dependencies (npm install)...")
        subprocess.check_call(["npm", "install"], cwd=FRONTEND)


def open_browser():
    time.sleep(5)
    webbrowser.open("http://localhost:5173")
    print("\n  Browser opened at http://localhost:5173\n")


if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("  PAFRL — Priority-Aware Adaptive Fuzzy RL")
    print("  React + Python3 Full-Stack Demo")
    print("=" * 55)

    check_python_deps()
    check_node()
    install_frontend_deps()

    print("\nStarting Flask backend (port 5000)...")
    backend_proc = subprocess.Popen(
        [sys.executable, "app.py"], cwd=BACKEND
    )

    time.sleep(2)

    print("Starting React dev server (port 5173)...")
    frontend_proc = subprocess.Popen(
        ["npm", "run", "dev"], cwd=FRONTEND
    )

    threading.Thread(target=open_browser, daemon=True).start()

    print("\n" + "-" * 55)
    print("  Backend:   http://localhost:5000/api/health")
    print("  Frontend:  http://localhost:5173")
    print("  Press Ctrl+C to stop both servers")
    print("-" * 55 + "\n")

    try:
        backend_proc.wait()
    except KeyboardInterrupt:
        print("\nStopping servers...")
        backend_proc.terminate()
        frontend_proc.terminate()
