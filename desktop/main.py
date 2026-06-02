#!/usr/bin/env python3
"""
Paper Clone Desktop - PyWebview Entry Point
Runs the app with embedded frontend + backend in a native window.
"""
import os
import sys
import threading
import subprocess
import webview
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent.resolve()
BACKEND_DIR = SCRIPT_DIR.parent / "backend"
FRONTEND_DIR = SCRIPT_DIR.parent / "frontend"

# Backend port
BACKEND_PORT = 3004


def start_backend():
    """Start the FastAPI backend server"""
    os.chdir(BACKEND_DIR)

    # Install dependencies if needed
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt"])

    # Start server
    import uvicorn
    from main import app
    uvicorn.run(app, host="127.0.0.1", port=BACKEND_PORT, log_level="warning")


def main():
    # Start backend in background thread
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()

    # Wait for backend to be ready
    import time
    time.sleep(2)

    # Build frontend if not built
    dist_dir = FRONTEND_DIR / "dist"
    if not dist_dir.exists():
        print("Building frontend...")
        os.chdir(FRONTEND_DIR)
        subprocess.run(["npm", "install", "-q"], check=True)
        subprocess.run(["npm", "run", "build"], check=True)

    # Create window
    window = webview.create_window(
        title="Paper Clone",
        url="http://localhost:5175",
        width=1400,
        height=900,
        min_size=(800, 600),
        resizable=True,
        js_api=None,
    )

    # Start pywebview
    webview.start(debug=True)


if __name__ == "__main__":
    main()
