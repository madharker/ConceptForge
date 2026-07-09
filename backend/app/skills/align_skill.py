"""Skill 4: 主流语境对齐 (mainstream context alignment).

Produces three layers of expression + a four-point diff, comparing the
student's own conclusion with the rigorous/academic formulation.
Mirrors spec "主流语境对齐" / "三层表述" + "差异说明".
"""
from __future__ import annotations

from typing import Optional

from app.llm_client import chat_json
from app.research_pedagogy import RESEARCH_PEDAGOGY_DEFINITION

SYSTEM_PROMPT = RESEARCH_PEDAGOGY_DEFINITION + (
    "你是研究式学习的概念对齐助手。请基于学生的临时结论，生成「三层表述」与「差异说明」，"
    "用中文回答，输出严格 JSON。\n"
    "要求：your_expression 必须逐字保留学生的原话（不得改写）；"
    "rigorous_rewrite 在不改变原意的前提下做严谨改写；"
    "mainstream_definition 给出教材/学术共同体的标准说法。"
    "\n对齐锚点：三层表述的对齐目标锚定到「把问题转化为概念」——"
    "rigorous_rewrite 在不改变原意下修正表述；mainstream_definition 给出学术共同体标准说法；"
    "差异说明聚焦「学生的问题意识 vs 主流概念定义」的落差，而非单纯纠错。"
)

SCHEMA_HINT = {
    "layers": {
        "your_expression": "学生原话（逐字保留）",
        "rigorous_rewrite": "严谨改写，不改变原意",
        "mainstream_definition": "教材/学术共同体标准说法",
    },
    "diff": {
        "got_right": "学生说对了什么",
        "missed": "学生漏掉了什么",
        "gap": "学生和主流定义差在哪里",
        "why_limited": "为什么主流定义要这样限定",
    },
}


def _build_user(topic: dict, submission: dict, evaluation: Optional[dict]) -> str:
    parts = [
        f"【课题】{topic.get('question', '')}",
        f"【课题背景】{topic.get('background', '')}",
        "【学生临时结论】" + submission.get("conclusion", ""),
    ]
    if evaluation:
        parts.append("【AI 评定（参考）】" + str(evaluation))
    parts.append(
        "请输出 JSON：layers 含 your_expression/rigorous_rewrite/mainstream_definition；"
        "diff 含 got_right/missed/gap/why_limited。"
    )
    return "\n".join(parts)


def _mock(topic: dict, submission: dict, evaluation: Optional[dict]) -> dict:
    """Deterministic alignment referencing entropy (thermo / stat mech / info)."""
    conclusion = submission.get("conclusion", "")
    return {
        "layers": {
            "your_expression": conclusion,
            "rigorous_rewrite": (
                "热机效率之所以存在上限，是因为热力学过程中总有一部分能量以热的形式"
                "不可逆地耗散到低温热源，无法再做功；这一不可逆性由状态函数「熵」描述，"
                "孤立系统的熵在自发过程中只增不减。"
            ),
            "mainstream_definition": (
                "熵 (S) 是热力学中描述系统状态不可逆性的广延量。对可逆过程，"
                "其微分定义为 dS = δQ_rev / T（克劳修斯定义）；在统计力学中"
                "S = k_B ln Ω（玻尔兹曼公式），与系统的微观状态数 Ω 相联系。"
                "热力学第二定律表述为：孤立系统的熵永不减少（ΔS_孤立 ≥ 0）。"
                "熵也是信息论中不确定性（香农熵 H = -Σ p_i log p_i）的度量原型。"
            ),
        },
        "diff": {
            "got_right": (
                "学生正确地认识到「能量损耗/废热」与效率上限相关，"
                "并直觉地把握到「存在一种衡量能量退化的量」，方向正确。"
            ),
            "missed": (
                "学生未明确熵的「状态函数」属性、未给出可逆过程的定量定义 dS=δQ_rev/T，"
                "也未联系到统计力学（玻尔兹曼公式）与信息论层面。"
            ),
            "gap": (
                "学生的表述停留在「能量被浪费」的日常语言层面，"
                "而主流定义把熵严格限定为可由热量与温度定义的状态函数，"
                "并与微观状态数、信息不确定性形成统一数学结构。"
            ),
            "why_limited": (
                "主流定义之所以要求「可逆过程 δQ_rev/T」，是因为只有可逆路径下"
                "δQ/T 才是状态函数的微分；不可逆过程中 δQ/T 会低估熵变。"
                "限定为状态函数后，熵才能脱离具体过程、用于判断过程方向与自发性，"
                "并跨学科（热力学/统计力学/信息论）保持一致。"
            ),
        },
    }


def align(topic: dict, submission: dict, evaluation: Optional[dict] = None) -> dict:
    """Run the alignment (three layers + diff).

    Guarantees that ``layers.your_expression`` is the student's conclusion
    verbatim, regardless of what the LLM returns.
    """
    user = _build_user(topic, submission, evaluation)
    data = chat_json(
        SYSTEM_PROMPT,
        user,
        schema_hint=SCHEMA_HINT,
        mock=lambda: _mock(topic, submission, evaluation),
    )

    # Defensive normalization for the LLM path.
    data.setdefault("layers", {})
    data.setdefault("diff", {})
    layers = data["layers"] if isinstance(data["layers"], dict) else {}
    diff = data["diff"] if isinstance(data["diff"], dict) else {}

    layers.setdefault("rigorous_rewrite", "")
    layers.setdefault("mainstream_definition", "")
    diff.setdefault("got_right", "")
    diff.setdefault("missed", "")
    diff.setdefault("gap", "")
    diff.setdefault("why_limited", "")

    # CONTRACT: your_expression must be the student's original conclusion verbatim.
    conclusion = submission.get("conclusion", "")
    layers["your_expression"] = conclusion

    data["layers"] = layers
    data["diff"] = diff
    return data
