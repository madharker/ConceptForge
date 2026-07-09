"""ConceptForge skills package.

Each skill is independently callable and returns plain JSON-serializable dicts:
- topic_skill.generate_topic          -> 课题生成
- collect_skill.collect                -> 5 步研究收集 (纯校验/归一化)
- evaluate_skill.evaluate              -> AI 过程评定 (五维)
- align_skill.align                    -> 主流语境对齐 (三层 + 差异)
- style_summary_skill.summarize_style  -> 风格与质量总结 (仅依据课题 + 学生回答)
"""
