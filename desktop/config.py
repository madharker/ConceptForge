"""User config persistence for the ConceptForge desktop app.

Stores LLM credentials (base_url, api_key, model) in a JSON file under the
user's OS-specific config directory:
- Windows: %APPDATA%/ConceptForge/config.json
- macOS:   ~/Library/Application Support/ConceptForge/config.json
- Linux:   ~/.config/conceptforge/config.json (XDG_CONFIG_HOME if set)
"""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path
from typing import Optional

APP_NAME = "ConceptForge"

def config_dir() -> Path:
    # Windows
    if os.name == "nt":
        base = os.environ.get("APPDATA") or str(Path.home())
        return Path(base) / APP_NAME
    # macOS
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    # Linux / other
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "conceptforge"

def config_path() -> Path:
    return config_dir() / "config.json"

def load_config() -> dict:
    """Return saved config dict, or empty defaults if none/invalid."""
    defaults = {"base_url": "", "api_key": "", "model": "gpt-4o-mini"}
    p = config_path()
    if not p.exists():
        return defaults
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        # merge with defaults to guarantee keys
        return {**defaults, **data}
    except Exception:
        return defaults

def save_config(cfg: dict) -> None:
    """Persist config to disk. Creates dir if needed."""
    config_dir().mkdir(parents=True, exist_ok=True)
    # only persist known keys
    clean = {
        "base_url": (cfg.get("base_url") or "").strip(),
        "api_key": (cfg.get("api_key") or "").strip(),
        "model": (cfg.get("model") or "gpt-4o-mini").strip(),
    }
    config_path().write_text(json.dumps(clean, ensure_ascii=False, indent=2), encoding="utf-8")
