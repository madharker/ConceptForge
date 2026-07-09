"""ConceptForge orchestration harness.

The Harness ties the skills together into the full learning closed-loop:
    课题生成 -> (5 步研究收集) -> AI 过程评定 -> 主流语境对齐 -> 风格与质量总结

It is deliberately thin: it only sequences skill calls and persists results
into the in-memory store. ``evaluate_and_align`` runs only the evaluate +
align stages (unchanged contract); ``evaluate_align_summarize`` extends that
with the style/quality summary step so the harness remains the single
orchestrator of the full 5-skill pipeline.
"""
from __future__ import annotations

from typing import Optional

from app import store
from app.skills import (
    align_skill,
    collect_skill,
    evaluate_skill,
    style_summary_skill,
    topic_skill,
)


class Harness:
    """Orchestrates the ConceptForge skill pipeline."""

    def new_topic(self, subject_hint: Optional[str] = None) -> dict:
        """Generate a topic (question form + background) and store it."""
        topic = topic_skill.generate_topic(subject_hint)
        store.put_topic(topic)
        return topic

    def run_full_pipeline(
        self,
        subject_hint: Optional[str] = None,
        submission: Optional[dict] = None,
    ) -> dict:
        """Run the pipeline.

        Stage 1: generate + store a topic.
        Stage 2 (optional): if a ``submission`` dict (5 fields) is provided,
            validate it via collect_skill, then run evaluate + align and
            return the combined result.

        When ``submission`` is None the harness returns the generated topic and
        signals that it is awaiting an external submission (the normal
        interactive flow: the frontend collects the 5 steps from the student
        before POSTing back).
        """
        topic = topic_skill.generate_topic(subject_hint)
        store.put_topic(topic)

        if submission is None:
            return {
                "topic": topic,
                "status": "awaiting_submission",
                "evaluation": None,
                "alignment": None,
            }

        # Stage 2: validate + evaluate + align.
        normalized = collect_skill.collect(submission)
        result = self.evaluate_and_align(topic, normalized)
        return {
            "topic": topic,
            "submission": normalized,
            "status": "complete",
            **result,
        }

    def evaluate_and_align(
        self,
        topic: dict,
        submission: dict,
        evaluation: Optional[dict] = None,
    ) -> dict:
        """Run AI evaluation then mainstream alignment on a submission.

        Args:
            topic: dict with question/background.
            submission: normalized 5-field dict.
            evaluation: optional precomputed evaluation; if None it is computed.
        Returns:
            {"evaluation": {...five dims...}, "alignment": {"layers","diff"}}
        """
        if evaluation is None:
            evaluation = evaluate_skill.evaluate(topic, submission)
        alignment = align_skill.align(topic, submission, evaluation)
        return {"evaluation": evaluation, "alignment": alignment}

    def summarize_style(self, topic: dict, submission: dict) -> dict:
        """Run the style & quality summary skill (closing step of the loop).

        Independent of evaluate + align: only the topic and the student's own
        5-step research are read.
        """
        return style_summary_skill.summarize_style(topic, submission)

    def evaluate_align_summarize(self, topic: dict, submission: dict) -> dict:
        """Run evaluate + align, then the style/quality summary.

        Convenience wrapper for the full 3-result pipeline used by the
        submissions router. ``evaluate_and_align`` is left unchanged so
        existing callers keep working.

        Returns:
            {"evaluation": ..., "alignment": ..., "style_summary": ...}
        """
        result = self.evaluate_and_align(topic, submission)
        result["style_summary"] = self.summarize_style(topic, submission)
        return result


# Module-level singleton for routers / scripts to reuse.
harness = Harness()
