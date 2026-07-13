"""ConceptForge desktop app entry point.

Starts the FastAPI backend (which also serves the built frontend via
StaticFiles mounted at "/") on a random localhost port, then opens the
app in a pywebview native window pointing at the backend's HTTP origin.

Loading the frontend over http:// from the backend (instead of file://)
is deliberate: under file://, pywebview's <script src="./__port__.js">
bootstrap is unreliable across backends (WebView2/EdgeChromium sometimes
silently skips it), which left window.__CF_PORT__ undefined and made
api.js's `new URL(\`${BASE}/api/...\`)` throw "Invalid URL". Serving
the frontend from the same HTTP origin as the API removes that whole
class of file:// quirks: scripts load normally, fetch is same-origin,
and the port is passed via a ?port= query string that the frontend
reads through URLSearchParams.

This is the pure-pywebview variant for the double-script (setup.bat +
run.bat) flow. Running under a normal Python interpreter, pywebview's
WinForms backend (pythonnet) initializes without issue — the pythonnet
problems only occur under PyInstaller frozen mode, which this branch
does not use.
"""
from __future__ import annotations
import socket
import sys
import threading
import time
import urllib.request
from pathlib import Path

import uvicorn
import webview

# PyInstaller frozen mode: bundled resources live under sys._MEIPASS
if getattr(sys, "frozen", False):
    _BASE_DIR = Path(sys._MEIPASS)
    DESKTOP_DIR = _BASE_DIR / "desktop"
    BACKEND_DIR = _BASE_DIR / "backend"
else:
    DESKTOP_DIR = Path(__file__).resolve().parent
    BACKEND_DIR = DESKTOP_DIR.parent / "backend"
ASSETS_DIR = DESKTOP_DIR / "assets"


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def start_backend(port: int):
    """Run the FastAPI backend in a daemon thread."""
    try:
        print(f"[backend] starting on http://127.0.0.1:{port}", flush=True)
        if str(BACKEND_DIR) not in sys.path:
            sys.path.insert(0, str(BACKEND_DIR))
        if str(DESKTOP_DIR.parent) not in sys.path:
            sys.path.insert(0, str(DESKTOP_DIR.parent))
        from desktop.config import load_config
        from app.llm_client import set_runtime_config
        cfg = load_config()
        if cfg.get("api_key"):
            set_runtime_config(cfg)
        uvicorn.run(
            "desktop.app:app",
            host="127.0.0.1",
            port=port,
            log_level="warning",
        )
    except Exception:
        import traceback
        print("[backend] FAILED to start:", flush=True)
        traceback.print_exc()


def main():
    port = find_free_port()
    # Start backend in daemon thread (dies with main thread)
    t = threading.Thread(target=start_backend, args=(port,), daemon=True)
    t.start()

    # Wait for backend to be ready
    backend_ready = False
    for _ in range(50):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=1)
            backend_ready = True
            break
        except Exception:
            time.sleep(0.2)

    if not backend_ready:
        print(f"[main] backend did not become ready on port {port}", flush=True)
        return

    print(f"[main] backend ready on port {port}", flush=True)

    # Load the frontend from the backend's HTTP origin (StaticFiles mount at "/").
    # Same-origin => no CORS, no file:// script-loading quirks.
    # ?port= is read by frontend api.js via URLSearchParams so it can build
    # absolute API URLs (new URL() requires an absolute base).
    if (ASSETS_DIR / "index.html").exists():
        url = f"http://127.0.0.1:{port}/?port={port}"
    else:
        print(f"[main] WARNING: {ASSETS_DIR / 'index.html'} not found", flush=True)
        url = f"http://127.0.0.1:{port}/?port={port}"

    print(f"[main] opening pywebview window: {url}", flush=True)
    webview.create_window("ConceptForge", url, width=1100, height=780)
    webview.start()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        print("[main] FATAL:", flush=True)
        traceback.print_exc()
    finally:
        # Keep console open on crash so the error is readable
        print("\n[main] Press Enter to exit...", flush=True)
        try:
            input()
        except EOFError:
            pass
