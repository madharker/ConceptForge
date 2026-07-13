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

# PyInstaller frozen mode: bundled resources live under sys._MEIPASS
# (in PyInstaller 6.x onedir mode, this is the _internal/ folder next to the exe).
# In source mode, just use the normal __file__-relative paths.
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
    try:
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
        print(f"[backend] starting on http://127.0.0.1:{port}", flush=True)
        uvicorn.run("desktop.app:app", host="127.0.0.1", port=port, log_level="warning")
    except Exception:
        import traceback
        print("[backend] FAILED to start:", flush=True)
        traceback.print_exc()

def inject_port(port: int) -> bool:
    """Write a small JS file the frontend imports to know the backend port.

    Returns True if written successfully, False if the assets dir is not
    writable (e.g. installed under Program Files). In that case the caller
    falls back to passing the port via URL query string.
    """
    bootstrap = ASSETS_DIR / "__port__.js"
    try:
        bootstrap.write_text(f"window.__CF_PORT__={port};", encoding="utf-8")
        return True
    except (PermissionError, OSError):
        return False

def main():
    port = find_free_port()
    # Start backend in daemon thread (dies with main thread)
    t = threading.Thread(target=start_backend, args=(port,), daemon=True)
    t.start()
    # Wait for backend to be ready
    import urllib.request
    ready = False
    for i in range(50):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=1)
            ready = True
            break
        except Exception:
            time.sleep(0.2)
    if not ready:
        print(f"[main] backend did not become ready on port {port} after 10s", flush=True)
        print("[main] check the [backend] traceback above; press Enter to exit", flush=True)
        try:
            input()
        except EOFError:
            pass
        return
    print(f"[main] backend ready on port {port}", flush=True)
    # Inject port into frontend
    port_written = inject_port(port)
    # Determine which frontend to load
    index = ASSETS_DIR / "index.html"
    if index.exists():
        url = index.as_uri()
        # Fallback: if __port__.js couldn't be written, pass port via query
        if not port_written:
            url = f"{url}?port={port}"
    else:
        # Dev fallback: assume vite dev server at 5174
        url = "http://localhost:5174"
        print(f"[dev] assets/index.html not found, loading {url}")
    webview.create_window("ConceptForge", url, width=1100, height=780)
    webview.start()
    # Window closed — process exits, daemon thread dies

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
