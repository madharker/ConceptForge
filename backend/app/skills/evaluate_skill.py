"""Skill 3: AI 过程评定 (AI process evaluation).

Evaluates the student's 5-step research process along five dimensions.
Returns structured JSON. Mirrors spec "AI 过程评定" / "五维评定".
"""
from __future__ import annotations

from typing import Optional

from app.llm_client import chat_json
from app.research_pedagogy import RESEARCH_PEDAGOGY_DEFINITION

SYSTEM_PROMPT = RESEARCH_PEDAGOGY_DEFINITION + (
    "你是研究式学习的评定助手，从五个维度评估学生的研究过程，用中文回答，输出严格 JSON。\n"
    "五维评定锚点：\n"
    "- problem_understanding：是否抓住「为什么需要这个概念」的核心，而非答非所问；\n"
    "- evidence_quality：证据是否服务于「逼近概念」，而非堆砌无关资料；\n"
    "- reasoning_chain：从猜想到结论是否经历「证据-矛盾-修正」闭环，而非直线跳到结论；\n"
    "- concept_boundary：是否区分目标概念与相邻概念，而非泛化混淆；\n"
    "- contradiction_handling：是否正面回应矛盾并据此修正，而非回避或硬凑。"
)

SCHEMA_HINT = {
    "problem_understanding": {"verdict": "简短评定", "detail": "具体说明"},
    "evidence_quality": {"verdict": "简短评定", "detail": "具体说明"},
    "reasoning_chain": {"verdict": "简短评定", "detail": "具体说明"},
    "concept_boundary": {"verdict": "简短评定", "detail": "具体说明"},
    "contradiction_handling": {"verdict": "简短评定", "detail": "具体说明"},
}

DIMENSIONS = (
    "problem_understanding",   # 是否抓住原始问题的核心
    "evidence_quality",        # 引用的资料是否可靠、相关
    "reasoning_chain",         # 是否有跳步、循环论证或逻辑断裂
    "concept_boundary",        # 是否混淆了相邻概念
    "contradiction_handling",  # 遇到冲突时是回避还是正面回应
)


def _build_user(topic: dict, submission: dict) -> str:
    return (
        f"【课题】{topic.get('question', '')}\n"
        f"【课题背景】{topic.get('background', '')}\n\n"
        "【学生 5 步研究】\n"
        f"原始猜想：{submission.get('guess', '')}\n"
        f"收集证据：{submission.get('evidence', '')}\n"
        f"遇到矛盾：{submission.get('contradiction', '')}\n"
        f"修正理解：{submission.get('revision', '')}\n"
        f"临时结论：{submission.get('conclusion', '')}\n\n"
        "请从以下五个维度评估，每个维度给出简短 verdict 与具体 detail：\n"
        "1) problem_understanding：是否抓住原始问题的核心；\n"
        "2) evidence_quality：引用的资料是否可靠、相关；\n"
        "3) reasoning_chain：是否有跳步、循环论证或逻辑断裂；\n"
        "4) concept_boundary：是否混淆了相邻概念；\n"
        "5) contradiction_handling：遇到冲突时是回避还是正面回应。\n"
        "输出 JSON。"
    )


def _mock(topic: dict, submission: dict) -> dict:
    """Deterministic verdicts referencing the entropy example."""
    return {
        "problem_understanding": {
            "verdict": "良好",
            "detail": "学生抓住了「热机效率存在不可消除的上限」这一核心问题，"
                     "但未点明「热传递的不可逆性」才是上限的根因。",
        },
        "evidence_quality": {
            "verdict": "中等",
            "detail": "引用了卡诺循环与热力学第二定律，方向可靠；"
                     "但缺乏对可逆/不可逆过程的具体量化证据（如 dS=δQ_rev/T）。",
        },
        "reasoning_chain": {
            "verdict": "基本连贯，存在一处跳步",
            "detail": "从「热量散失」到「存在熵增」的推理成立，"
                     "但中间跳过了「为什么废热不可逆」的论证环节。",
        },
        "concept_boundary": {
            "verdict": "需澄清",
            "detail": "学生将「熵」与「混乱度」直接等同，未区分宏观热力学熵与统计熵的适用边界。",
        },
        "contradiction_handling": {
            "verdict": "正面回应",
            "detail": "学生在「理想可逆热机效率 100%」与「现实中效率远低于此」之间发现矛盾，"
                     "并尝试用不可逆损耗解释，处理态度积极。",
        },
    }


def evaluate(topic: dict, submission: dict) -> dict:
    """Run the five-dimension evaluation.

    Args:
        topic: dict with question/background.
        submission: dict with the 5 research fields.
    Returns:
        Evaluation dict with five dimensions, each {verdict, detail}.
    """
    user = _build_user(topic, submission)
    data = chat_json(
        SYSTEM_PROMPT,
        user,
        schema_hint=SCHEMA_HINT,
        mock=lambda: _mock(topic, submission),
    )
    # Ensure all five dimensions exist (defensive normalization for the LLM path).
    for dim in DIMENSIONS:
        if dim not in data:
            data[dim] = {"verdict": "未知", "detail": ""}
        else:
            entry = data[dim] or {}
            entry.setdefault("verdict", "未知")
            entry.setdefault("detail", "")
            data[dim] = entry
    return data


def evaluate_with_hint(topic: dict, submission: dict, evaluation: Optional[dict] = None) -> dict:
    """Backwards-friendly alias kept for clarity; delegates to evaluate()."""
    return evaluate(topic, submission)
