"""Skill 5: 风格与质量总结 (style & quality summary).

Closes the ConceptForge loop: produces a structured summary of the student's
answer STYLE and QUALITY. Deliberately independent of evaluate + align — it
reads ONLY the topic and the student's own 5-step research, so it can be run
on its own. The result is kept separate from the regular evaluation response
and only persisted in the backend store / returned via the dedicated
/style-summary endpoint.

Mirrors the chat_json + mock-lambda pattern used by evaluate_skill and
align_skill so the pipeline runs end-to-end without an LLM key.
"""
from __future__ import annotations

from app.llm_client import chat_json
from app.research_pedagogy import RESEARCH_PEDAGOGY_DEFINITION

SYSTEM_PROMPT = RESEARCH_PEDAGOGY_DEFINITION + (
    "你是研究式学习的过程总结助手，仅依据学生自己的 5 步研究回答，"
    "总结其回答风格与质量，用中文回答，输出严格 JSON。\n"
    "总结维度锚点：\n"
    "- expression_style：是否便于暴露思考过程，而非仅追求辞藻；\n"
    "- thinking_traits：是否重证据、善对比、主动自我修正（研究式学习推崇）；\n"
    "- quality_overall：是否完成「问题→概念」的认知跃迁；\n"
    "- improvement：针对「如何更好逼近概念」的具体建议，而非泛泛鼓励。"
)

SCHEMA_HINT = {
    "expression_style": "表达风格：语言组织特征，如简洁/详尽、口语化/书面化、术语使用倾向",
    "thinking_traits": "思维特征：论证偏好，如重证据/重直觉、是否善于对比、是否主动自我修正",
    "quality_overall": "质量总评：对本课题回答的综合简评",
    "improvement": "改进建议：1-2 条针对本次回答的具体建议",
}

FIELDS = ("expression_style", "thinking_traits", "quality_overall", "improvement")


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
        "请仅依据以上学生自己的回答，从以下四个维度总结风格与质量，输出 JSON：\n"
        "1) expression_style（表达风格）：语言组织特征，如简洁/详尽、口语化/书面化、术语使用倾向；\n"
        "2) thinking_traits（思维特征）：论证偏好，如重证据/重直觉、是否善于对比、是否主动自我修正；\n"
        "3) quality_overall（质量总评）：对本课题回答的综合简评；\n"
        "4) improvement（改进建议）：1-2 条针对本次回答的具体建议。"
    )


def _mock(topic: dict, submission: dict) -> dict:
    """Deterministic summary referencing the entropy example."""
    return {
        "expression_style": (
            "语言偏书面化但不晦涩，行文较简洁；自觉使用「卡诺定理」「热力学第二定律」"
            "等术语支撑论点，但在涉及熵的本质时仍退回到「能量散失/废热」的日常表述，"
            "术语使用从「现象层」向「定义层」过渡但未完全到位。"
        ),
        "thinking_traits": (
            "明显重证据：以卡诺定理与第二定律为支点支撑结论，而非纯凭直觉；"
            "善于自我修正——主动承认「一开始以为是摩擦损耗」并改判为「物理规律本身的限制」；"
            "对比意识较弱，未将「可逆/不可逆过程」做对照论证，导致结论的边界感不足。"
        ),
        "quality_overall": (
            "本次回答准确抓住了「热机效率存在不可消除的上限」这一核心，并能在证据驱动下"
            "修正最初「工程损耗」的直觉判断，闭环完成度较高；不足在于对熵作为状态函数的"
            "定量定义（dS=δQ_rev/T）与统计/信息论层面的延伸缺失，论证停留在定性层面。"
        ),
        "improvement": (
            "1) 在「收集证据」环节补充一条可逆过程的定量依据（如 dS=δQ_rev/T），"
            "把效率上限从「能量散失」推进到「熵增不可逆」的根因；"
            "2) 在「临时结论」中显式对比「可逆过程效率上限」与「不可逆过程效率损失」，"
            "厘清「物理规律上限」与「工程损耗」两条不同的边界。"
        ),
    }


def summarize_style(topic: dict, submission: dict) -> dict:
    """Generate the style & quality summary.

    Intentionally independent of evaluate + align: only the topic and the
    student's own 5-step research are read.

    Args:
        topic: dict with question/background.
        submission: dict with the 5 research fields.
    Returns:
        Dict with expression_style / thinking_traits / quality_overall /
        improvement (all guaranteed present, missing -> "").
    """
    user = _build_user(topic, submission)
    data = chat_json(
        SYSTEM_PROMPT,
        user,
        schema_hint=SCHEMA_HINT,
        mock=lambda: _mock(topic, submission),
    )
    # Defensive normalization: ensure all 4 keys exist as strings.
    for field in FIELDS:
        value = data.get(field, "")
        if value is None or not isinstance(value, str):
            value = "" if value is None else str(value)
        data[field] = value
    return {field: data[field] for field in FIELDS}
