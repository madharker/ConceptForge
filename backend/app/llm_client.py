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

import collections
import json
import os
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Optional, Union

DEFAULT_MODEL = "gpt-4o-mini"

# 无活动超时（秒）：streaming 期间若 30s 内未收到任何新 chunk，判定模型异常暂停。
IDLE_TIMEOUT_SEC = 30.0
# 连接阶段超时（秒）：base_url 错误或不可达时快速失败。
CONNECT_TIMEOUT_SEC = 10.0

MockSpec = Union[dict, Callable[[], dict], None]

# Runtime config (desktop app injects via set_runtime_config).
# When None (default), falls back to env vars — preserving Web backend behavior.
_runtime_config: Optional[dict] = None

# ---------------------------------------------------------------------------
# LLM 调用日志缓冲（供桌面端「LLM 调用日志」面板轮询展示）
# ---------------------------------------------------------------------------
_LLM_LOGS: "collections.deque[dict]" = collections.deque(maxlen=50)


def get_recent_logs() -> list[dict]:
    """返回最近 50 条 LLM 调用日志（最新在前）。"""
    return list(_LLM_LOGS)


def clear_logs() -> None:
    """清空调用日志。"""
    _LLM_LOGS.clear()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _preview(s: Optional[str], n: int = 400) -> Optional[str]:
    if s is None:
        return None
    return s if len(s) <= n else s[:n] + "…"


def _log_start(call_id: str, model: str, system: str, user: str, mock: bool) -> None:
    _LLM_LOGS.appendleft({
        "call_id": call_id,
        "model": model,
        "mock": mock,
        "status": "running",
        "started_at": _now_iso(),
        "finished_at": None,
        "elapsed_ms": None,
        "chars_received": 0,
        "system_preview": _preview(system),
        "user_preview": _preview(user),
        "response_preview": None,
        "error": None,
    })


def _log_update(call_id: str, **fields: Any) -> None:
    for entry in _LLM_LOGS:
        if entry["call_id"] == call_id:
            entry.update(fields)
            return


def _log_finish(
    call_id: str,
    status: str,
    response: Optional[str] = None,
    error: Optional[str] = None,
    elapsed_ms: Optional[int] = None,
    chars: int = 0,
) -> None:
    _log_update(
        call_id,
        status=status,
        finished_at=_now_iso(),
        elapsed_ms=elapsed_ms,
        chars_received=chars,
        response_preview=_preview(response),
        error=error,
    )


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

    每次调用都会写入 ``_LLM_LOGS`` 缓冲区，供桌面端日志面板轮询展示。
    真实调用采用 streaming 模式，并通过 httpx 的 read timeout 检测「模型
    异常暂停」——若 {IDLE_TIMEOUT_SEC}s 内未收到任何新 chunk 即判定超时，
    立即向上抛出 ``RuntimeError``，前端可据此通知用户。
    """
    call_id = uuid.uuid4().hex[:8]

    if is_mock_mode():
        _log_start(call_id, "(mock)", system, user, mock=True)
        result = _resolve_mock(mock)
        _log_finish(
            call_id,
            status="success",
            response=json.dumps(result, ensure_ascii=False),
            elapsed_ms=0,
            chars=0,
        )
        return result

    cfg = _get_config()
    _log_start(call_id, cfg["model"], system, user, mock=False)

    # Lazy import so mock-only environments don't require the SDK at runtime.
    from openai import OpenAI  # type: ignore
    import httpx  # type: ignore

    # read timeout = 无活动超时；connect timeout = 连接阶段超时。
    # streaming 模式下，read timeout 作用于每次 chunk 读取——若模型暂停
    # 输出（IDLE_TIMEOUT_SEC 内无新数据），httpx 抛 ReadTimeout。
    timeout_cfg = httpx.Timeout(
        connect=CONNECT_TIMEOUT_SEC,
        read=IDLE_TIMEOUT_SEC,
        write=10.0,
        pool=10.0,
    )
    client = OpenAI(
        base_url=cfg["base_url"],
        api_key=cfg["api_key"],
        timeout=timeout_cfg,
    )

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

    start_ts = time.time()
    chunks: list[str] = []
    chars_so_far = 0
    try:
        stream = client.chat.completions.create(
            model=cfg["model"],
            messages=messages,
            temperature=0.2,
            response_format={"type": "json_object"},
            stream=True,
        )
        for chunk in stream:
            delta = ""
            if chunk.choices:
                delta = chunk.choices[0].delta.content or ""
            if delta:
                chunks.append(delta)
                chars_so_far += len(delta)
                # 实时更新已接收字符数，前端轮询时可见「正在输出」
                _log_update(call_id, chars_received=chars_so_far)
        content = "".join(chunks)
        result = _extract_json(content)
        elapsed_ms = int((time.time() - start_ts) * 1000)
        _log_finish(
            call_id,
            status="success",
            response=content,
            elapsed_ms=elapsed_ms,
            chars=chars_so_far,
        )
        return result
    except httpx.TimeoutException as exc:
        elapsed_ms = int((time.time() - start_ts) * 1000)
        msg = f"模型超时（{IDLE_TIMEOUT_SEC:.0f}s 内无输出，可能已异常暂停）: {exc}"
        _log_finish(
            call_id,
            status="timeout",
            error=msg,
            elapsed_ms=elapsed_ms,
            chars=chars_so_far,
        )
        raise RuntimeError(f"LLM 调用超时: {msg}") from exc
    except Exception as exc:  # pragma: no cover - network path, not tested here
        elapsed_ms = int((time.time() - start_ts) * 1000)
        _log_finish(
            call_id,
            status="failed",
            error=str(exc),
            elapsed_ms=elapsed_ms,
            chars=chars_so_far,
        )
        raise RuntimeError(f"LLM chat_json call failed: {exc}") from exc
