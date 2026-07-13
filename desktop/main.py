"""ConceptForge desktop app entry point.

Starts the FastAPI backend on a random localhost port, then opens the app
in a pywebview native window pointing at the bundled assets/index.html.

The frontend learns the backend port via one of two mechanisms:
  1. A bootstrap file `assets/__port__.js` written at runtime containing
     `window.__CF_PORT__=<port>;` (preferred — works under file://).
  2. A `?port=<port>` query string appended to the index URL (fallback
     when the assets directory is not writable, e.g. frozen EXE).

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


def inject_port(port: int) -> bool:
    """Write a bootstrap JS file telling the frontend which port to use.

    Returns True on success. Under file:// the frontend loads this script
    via a <script src="__port__.js"></script> tag; under http:// it is
    ignored (the frontend reads its own origin instead).
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

    # Tell the frontend which port the backend is on.
    port_written = inject_port(port)

    # Load the bundled frontend. Prefer file:// over the backend's static
    # mount so the window is independent of the backend serving path.
    index = ASSETS_DIR / "index.html"
    if index.exists():
        url = index.as_uri()
        if not port_written:
            url = f"{url}?port={port}"
    else:
        # Fallback: let the backend serve the frontend (if mounted).
        url = f"http://127.0.0.1:{port}"

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
