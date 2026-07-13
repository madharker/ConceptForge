"""ConceptForge desktop FastAPI app.

Mounts the existing backend routers (topics, submissions) AND adds /api/settings
endpoints so the desktop frontend's SettingsView can read/write LLM config
persistently and inject it into llm_client at runtime.

Also serves the built frontend (desktop/assets/) so the app can be opened
in a browser/Edge-app window without needing pywebview or pythonnet.
"""
from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Import existing routers (add backend to sys.path)
import sys
from pathlib import Path
if getattr(sys, "frozen", False):
    # PyInstaller frozen mode: resources are under sys._MEIPASS
    _BACKEND = Path(sys._MEIPASS) / "backend"
else:
    _BACKEND = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.routers import topics, submissions  # noqa: E402
from app.llm_client import (  # noqa: E402
    set_runtime_config,
    get_runtime_config,
    is_mock_mode,
    get_recent_logs,
    clear_logs,
)
from desktop.config import load_config, save_config  # noqa: E402

app = FastAPI(title="ConceptForge Desktop")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount existing routers — same /api/* paths as Web backend
app.include_router(topics.router)
app.include_router(submissions.router)


class SettingsModel(BaseModel):
    base_url: str = ""
    api_key: str = ""
    model: str = "gpt-4o-mini"


@app.get("/api/health")
def health():
    return {"status": "ok", "mock_mode": is_mock_mode()}


@app.get("/api/settings")
def get_settings():
    """Return current persisted LLM config + mock status."""
    cfg = load_config()
    return {
        "base_url": cfg.get("base_url", ""),
        "api_key": cfg.get("api_key", ""),
        "model": cfg.get("model", "gpt-4o-mini"),
        "mock_mode": is_mock_mode(),
    }


@app.put("/api/settings")
def put_settings(s: SettingsModel):
    """Persist config AND inject into llm_client immediately (no restart)."""
    cfg = {"base_url": s.base_url, "api_key": s.api_key, "model": s.model}
    save_config(cfg)
    set_runtime_config(cfg)
    return {"ok": True, "mock_mode": is_mock_mode()}


@app.post("/api/settings/test")
def test_connection(s: SettingsModel):
    """Send a minimal LLM request with the given (unsaved) config to verify it works."""
    from app.llm_client import chat_json
    # Temporarily inject the test config
    test_cfg = {"base_url": s.base_url, "api_key": s.api_key, "model": s.model}
    set_runtime_config(test_cfg)
    try:
        result = chat_json(
            system="You are a connection test. Reply with JSON.",
            user='{"ping":"pong"}',
            schema_hint={"ping": "string"},
            mock={"ping": "mock"},
        )
        # If result has ping key, it worked
        is_real = not is_mock_mode()
        return {"ok": True, "mock_mode": not is_real, "response": result}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        # Restore the persisted config (or None if none saved)
        persisted = load_config()
        if persisted.get("api_key"):
            set_runtime_config(persisted)
        else:
            set_runtime_config(None)


@app.get("/api/llm/logs")
def llm_logs():
    """返回最近 50 条 LLM 调用日志（最新在前）。

    每条日志包含：call_id, model, mock, status (running/success/failed/timeout),
    started_at, finished_at, elapsed_ms, chars_received, system_preview,
    user_preview, response_preview, error。

    前端轮询此端点即可实时观测 LLM 的输入输出与异常状态。
    """
    return {"logs": get_recent_logs()}


@app.delete("/api/llm/logs")
def llm_logs_clear():
    """清空日志。"""
    clear_logs()
    return {"ok": True}


# --- Static frontend serving ---
# Mount the built frontend (desktop/assets/) at "/" so the app can be
# opened directly via http://127.0.0.1:port/ in a browser/Edge-app window.
# Must be registered AFTER all /api/* routes so API requests take priority.
# StaticFiles(html=True) serves index.html at "/" automatically.
if getattr(sys, "frozen", False):
    _ASSETS = Path(sys._MEIPASS) / "desktop" / "assets"
else:
    _ASSETS = Path(__file__).resolve().parent / "assets"

if _ASSETS.is_dir():
    app.mount("/", StaticFiles(directory=str(_ASSETS), html=True), name="frontend")
