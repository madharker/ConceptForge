"""Skill 1: 课题生成 (topic generation).

Produces a research topic in QUESTION form (never a direct definition),
plus a short background. Mirrors spec requirement "课题生成（AI 提出课题）".
"""
from __future__ import annotations

import uuid
from typing import Optional

from app.llm_client import chat_json
from app.research_pedagogy import RESEARCH_PEDAGOGY_DEFINITION

SYSTEM_PROMPT = RESEARCH_PEDAGOGY_DEFINITION + (
    "你是研究式学习的课题设计助手。你必须以「问题」形式（而非直接给定义）提出研究课题，"
    "引导学习者围绕「为什么需要这个概念」展开研究。\n"
    "课题质量锚点：课题须能引出「问题→概念」的认知跃迁——以问题形式呈现、能引出该领域一个核心概念、"
    "能激发猜想与矛盾暴露、可在一轮 10-15 分钟研究中逼近；而非知识问答。\n"
    "输出严格 JSON，字段：id (字符串), question (问题文本), background (简短背景)。"
)

SCHEMA_HINT = {
    "id": "字符串，课题唯一标识",
    "question": "字符串，以问题形式呈现的课题",
    "background": "字符串，简短背景说明",
}

# Deterministic mock topic — the canonical "熵 (entropy)" example from the spec.
MOCK_TOPIC_NO_HINT = {
    "id": "topic-entropy-demo",
    "question": "为什么热机无论怎么改进，都不能把所有热量转化为有用功？",
    "background": (
        "19 世纪工程师卡诺在研究蒸汽机效率时发现：热从高温流向低温是不可逆的，"
        "总有一部分能量以「废热」形式散失。这背后隐藏着一个描述「能量品质退化」的物理量——熵。"
        "本课题引导你从热机效率出发，自行逼近「为什么存在无法消除的效率上限」这一核心问题。"
    ),
}


def _mock(subject: Optional[str]) -> dict:
    """Deterministic mock matching the entropy example."""
    if subject and subject.strip():
        s = subject.strip()
        return {
            "id": f"topic-{uuid.uuid4().hex[:8]}",
            "question": f"在「{s}」中，为什么存在一个反复出现、却难以用直觉直接解释的核心矛盾？",
            "background": (
                f"围绕「{s}」的研究课题：从工程师/科学家的真实困境出发，引导学生先猜想、再收集证据、"
                "再暴露矛盾，最终自行逼近该领域一个关键概念的本质。"
            ),
        }
    # No hint => the canonical entropy topic (matches spec example exactly).
    return dict(MOCK_TOPIC_NO_HINT)


def generate_topic(subject: Optional[str] = None) -> dict:
    """Generate a research topic (question form + background).

    Args:
        subject: optional subject hint, e.g. "热力学". None/empty => entropy example.
    Returns:
        dict with keys id, question, background.
    """
    subj = (subject or "").strip() or None
    hint = subj or "熵（entropy）"
    user = (
        f"请围绕学科主题「{hint}」提出一个研究课题。要求：\n"
        "1) 必须以「问题」形式呈现，不能直接给出定义；\n"
        "2) 问题应能引出该领域一个核心概念；\n"
        "3) 附一段简短背景说明该问题为何重要。\n"
        "请输出 JSON。"
    )

    data = chat_json(
        SYSTEM_PROMPT,
        user,
        schema_hint=SCHEMA_HINT,
        mock=lambda: _mock(subj),
    )

    # Normalize / guarantee required fields.
    if not data.get("id"):
        data["id"] = f"topic-{uuid.uuid4().hex[:8]}"
    if not data.get("question"):
        # Never return an empty question — fall back to mock content.
        fallback = _mock(subj)
        data["question"] = fallback["question"]
        data.setdefault("background", fallback["background"])
    data.setdefault("background", "")
    return data
