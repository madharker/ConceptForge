"""Skill 2: 5 步研究收集 (5-step research collection).

Pure validation + normalization — no LLM. Validates that all 5 steps are
non-empty strings and returns a normalized ResearchSubmission dict.

The 5 fields & their guiding prompts are defined here (single source of truth)
and re-exported via schemas.RESEARCH_FIELDS / RESEARCH_PROMPTS.
"""
from __future__ import annotations

from app.schemas import RESEARCH_FIELDS, RESEARCH_PROMPTS

__all__ = ["RESEARCH_FIELDS", "RESEARCH_PROMPTS", "CollectValidationError", "collect"]


class CollectValidationError(ValueError):
    """Raised when a 5-step field is missing or empty (-> 422 in routers)."""


def collect(data: dict) -> dict:
    """Validate & normalize a 5-step research submission.

    Args:
        data: dict possibly containing guess/evidence/contradiction/revision/conclusion.
    Returns:
        A dict with exactly the 5 canonical fields, whitespace-trimmed.
    Raises:
        CollectValidationError: if any of the 5 fields is missing or blank.
    """
    if not isinstance(data, dict):
        raise CollectValidationError("提交内容必须是 JSON 对象。")

    normalized: dict = {}
    for field in RESEARCH_FIELDS:
        if field not in data:
            raise CollectValidationError(
                f"缺少字段「{field}」（提示：{RESEARCH_PROMPTS[field]}）"
            )
        value = data[field]
        if not isinstance(value, str):
            raise CollectValidationError(f"字段「{field}」必须是字符串。")
        if not value.strip():
            raise CollectValidationError(
                f"字段「{field}」不能为空（提示：{RESEARCH_PROMPTS[field]}）"
            )
        normalized[field] = value.strip()
    return normalized
