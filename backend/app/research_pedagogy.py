"""Shared ConceptForge research-based-learning pedagogy definition.

All four AI skills (topic / evaluate / align / style_summary) reference the
term 「研究式学习」 in their system prompts. To keep LLM output consistent,
that term is defined once here and PREPENDED to every skill's SYSTEM_PROMPT.

This module is PROMPT-ONLY: it changes no API contract, schema, harness,
store, or mock data. Each skill additionally appends its own per-skill
anchor after the definition (see the individual skill files).
"""

RESEARCH_PEDAGOGY_DEFINITION = (
    "【ConceptForge 研究式学习理念】\n"
    "本系统所说的「研究式学习」特指 ConceptForge 理念，包含四条核心：\n"
    "1. 先研究后定义：学习者先围绕真实问题做一轮小型研究，再与主流定义对齐，而非先背定义。\n"
    "2. AI 退后一步：AI 只设计问题与提供反馈，把「把问题转化为概念」的认知劳动还给学习者。\n"
    "3. 5 步认知跃迁：原始猜想 → 收集证据 → 遇到矛盾 → 修正理解 → 临时结论，矛盾暴露是关键节点。\n"
    "4. 逻辑自洽优先：临时结论不要求与教材一致，只要求基于证据的逻辑自洽；对齐主流是事后校准。\n\n"
)
