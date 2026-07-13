"""ConceptForge desktop app entry point.

Starts the FastAPI backend (which also serves the built frontend) on a
random localhost port, then opens the app in Edge's --app mode — a
chromeless window that looks like a native app.

This replaces pywebview, whose default Windows backend (WinForms) depends
on pythonnet (CLR bridge). pythonnet's Python.Runtime.dll fails to
initialize under PyInstaller 6.x, causing a crash at webview.start().
Using Edge --app mode bypasses pythonnet entirely and relies on the
system WebView2/Edge runtime (preinstalled on Win10/11).

For development, the backend serves desktop/assets/index.html if it
exists; otherwise point a browser at the dev server.
"""
from __future__ import annotations
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import uvicorn

# PyInstaller frozen mode: bundled resources live under sys._MEIPASS
if getattr(sys, "frozen", False):
    _BASE_DIR = Path(sys._MEIPASS)
    DESKTOP_DIR = _BASE_DIR / "desktop"
    BACKEND_DIR = _BASE_DIR / "backend"
else:
    DESKTOP_DIR = Path(__file__).resolve().parent
    BACKEND_DIR = DESKTOP_DIR.parent / "backend"


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


def open_app_window(url: str, width: int = 1100, height: int = 780) -> bool:
    """Open url in Edge --app mode (window without browser chrome).

    Falls back to the default browser if Edge is not found.
    Returns True if Edge was used.
    """
    if sys.platform != "win32":
        import webbrowser
        webbrowser.open(url)
        return False

    # Common Edge installation paths on Windows
    edge_candidates = [
        os.environ.get("EDGE_PATH", ""),
        shutil.which("msedge"),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    for path in edge_candidates:
        if path and os.path.isfile(path):
            try:
                subprocess.Popen([
                    path,
                    f"--app={url}",
                    f"--window-size={width},{height}",
                    "--disable-extensions",
                    "--no-default-browser-check",
                    "--no-first-run",
                ])
                return True
            except OSError:
                continue

    # Fallback: default browser
    import webbrowser
    webbrowser.open(url)
    return False


def main():
    port = find_free_port()
    # Start backend in daemon thread (dies with main thread)
    t = threading.Thread(target=start_backend, args=(port,), daemon=True)
    t.start()

    # Wait for backend to be ready
    import urllib.request
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

    # Open app window — backend serves the frontend at /
    url = f"http://127.0.0.1:{port}"
    used_edge = open_app_window(url)
    if used_edge:
        print(f"[main] opened in Edge app mode: {url}", flush=True)
    else:
        print(f"[main] opened in default browser: {url}", flush=True)

    # Keep main thread alive until backend thread ends or Ctrl+C.
    # The user closes the app by closing this console window or Ctrl+C.
    try:
        while t.is_alive():
            t.join(timeout=1)
    except KeyboardInterrupt:
        print("\n[main] shutting down...")


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
