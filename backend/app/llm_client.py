"""OpenAI-compatible LLM client with deterministic mock fallback.

Public entry point: ``chat_json(system, user, schema_hint, mock=None) -> dict``

Behaviour:
- If ``CF_LLM_API_KEY`` is unset or empty, the client runs in MOCK mode and
  returns the ``mock`` payload (a dict, or a zero-arg callable returning a dict).
  This lets the full ConceptForge pipeline run end-to-end with zero credentials.
- Otherwise it performs a real chat completion against an OpenAI-compatible
  endpoint (configured via ``CF_LLM_BASE_URL`` / ``CF_LLM_MODEL``) and parses
  the response as JSON.

Config sources (checked in order):
- Runtime config: injected via ``set_runtime_config(cfg)``. Used by the desktop
  app settings page. When set, it takes precedence over env vars. Pass ``None``
  to clear and revert to env vars (Web backend default path).
- Env vars (fallback when no runtime config is set):
  - ``CF_LLM_BASE_URL``  base url of the OpenAI-compatible API
  - ``CF_LLM_API_KEY``   api key; empty/missing => mock mode
  - ``CF_LLM_MODEL``     model name (default ``gpt-4o-mini``)
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Callable, Optional, Union

DEFAULT_MODEL = "gpt-4o-mini"

MockSpec = Union[dict, Callable[[], dict], None]

# Runtime config (desktop app injects via set_runtime_config).
# When None (default), falls back to env vars — preserving Web backend behavior.
_runtime_config: Optional[dict] = None


def set_runtime_config(cfg: Optional[dict]) -> None:
    """Inject runtime LLM config (desktop app settings page).

    cfg shape: {"base_url": str|None, "api_key": str, "model": str}
    Pass None to clear and revert to env vars.
    """
    global _runtime_config
    _runtime_config = dict(cfg) if cfg else None


def get_runtime_config() -> Optional[dict]:
    """Return current runtime config (for inspection/testing)."""
    return dict(_runtime_config) if _runtime_config else None


def is_mock_mode() -> bool:
    """True when no API key is configured (mock fallback active)."""
    if _runtime_config is not None:
        return not (_runtime_config.get("api_key") or "").strip()
    return not (os.getenv("CF_LLM_API_KEY") or "").strip()


def _get_config() -> dict:
    if _runtime_config is not None:
        return {
            "base_url": _runtime_config.get("base_url") or None,
            "api_key": (_runtime_config.get("api_key") or "").strip(),
            "model": (_runtime_config.get("model") or DEFAULT_MODEL).strip(),
        }
    # Fallback: env vars (Web backend path — unchanged)
    return {
        "base_url": (os.getenv("CF_LLM_BASE_URL") or "").strip() or None,
        "api_key": (os.getenv("CF_LLM_API_KEY") or "").strip(),
        "model": (os.getenv("CF_LLM_MODEL") or DEFAULT_MODEL).strip(),
    }


def _extract_json(text: str) -> dict:
    """Best-effort parse of a JSON object out of an LLM response string."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Fallback: pull out the first {...} block.
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        return json.loads(match.group(0))
    raise ValueError(f"LLM response was not valid JSON: {text[:200]!r}")


def _resolve_mock(mock: MockSpec) -> dict:
    if mock is None:
        return {}
    if callable(mock):
        return mock()
    return dict(mock)


def chat_json(
    system: str,
    user: str,
    schema_hint: Optional[dict] = None,
    mock: MockSpec = None,
) -> dict[str, Any]:
    """Call the LLM and return parsed JSON. Falls back to mock when no API key.

    Args:
        system: system prompt.
        user: user prompt.
        schema_hint: optional description of the expected JSON shape; appended
            to the user prompt to steer structured output.
        mock: when in mock mode (no API key), this dict (or zero-arg callable
            returning a dict) is returned instead of calling the LLM.
    """
    if is_mock_mode():
        return _resolve_mock(mock)

    cfg = _get_config()
    # Lazy import so mock-only environments don't require the SDK at runtime.
    from openai import OpenAI  # type: ignore

    client = OpenAI(base_url=cfg["base_url"], api_key=cfg["api_key"])

    user_content = user
    if schema_hint:
        user_content += "\n\n请严格输出 JSON，schema 说明：" + json.dumps(
            schema_hint, ensure_ascii=False
        )
    user_content += '\n\n只输出 JSON 对象本身，不要包含 ```json 代码块或额外说明。'

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_content},
    ]

    try:
        resp = client.chat.completions.create(
            model=cfg["model"],
            messages=messages,
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content or ""
        return _extract_json(content)
    except Exception as exc:  # pragma: no cover - network path, not tested here
        # If the real call fails, surface a clear error rather than crashing
        # the pipeline silently. Callers may choose to retry/fallback.
        raise RuntimeError(f"LLM chat_json call failed: {exc}") from exc
