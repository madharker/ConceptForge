"""ConceptForge desktop app entry point.

Starts the FastAPI backend on a random localhost port in a background thread,
writes the port into the frontend's bootstrap file, then opens a PyWebView
window loading the built frontend (desktop/assets/index.html).

For development, if assets/index.html doesn't exist, falls back to loading
desktop/frontend/index.html via a dev server URL passed as --dev arg.
"""
from __future__ import annotations
import os
import socket
import sys
import threading
import time
from pathlib import Path

import uvicorn
import webview

DESKTOP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = DESKTOP_DIR.parent / "backend"
ASSETS_DIR = DESKTOP_DIR / "assets"

def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]

def start_backend(port: int):
    # Ensure backend importable
    if str(BACKEND_DIR) not in sys.path:
        sys.path.insert(0, str(BACKEND_DIR))
    # Ensure desktop importable
    if str(DESKTOP_DIR.parent) not in sys.path:
        sys.path.insert(0, str(DESKTOP_DIR.parent))
    # Load persisted config into llm_client
    from desktop.config import load_config
    from app.llm_client import set_runtime_config
    cfg = load_config()
    if cfg.get("api_key"):
        set_runtime_config(cfg)
    uvicorn.run("desktop.app:app", host="127.0.0.1", port=port, log_level="warning")

def inject_port(port: int):
    """Write a small JS file the frontend imports to know the backend port."""
    bootstrap = ASSETS_DIR / "__port__.js"
    bootstrap.write_text(f"window.__CF_PORT__={port};", encoding="utf-8")

def main():
    port = find_free_port()
    # Start backend in daemon thread (dies with main thread)
    t = threading.Thread(target=start_backend, args=(port,), daemon=True)
    t.start()
    # Wait for backend to be ready
    import urllib.request
    for _ in range(50):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=1)
            break
        except Exception:
            time.sleep(0.2)
    # Inject port into frontend
    inject_port(port)
    # Determine which frontend to load
    index = ASSETS_DIR / "index.html"
    if index.exists():
        url = index.as_uri()
    else:
        # Dev fallback: assume vite dev server at 5174
        url = "http://localhost:5174"
        print(f"[dev] assets/index.html not found, loading {url}")
    webview.create_window("ConceptForge", url, width=1100, height=780)
    webview.start()
    # Window closed — process exits, daemon thread dies

if __name__ == "__main__":
    main()
