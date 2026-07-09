"""In-memory storage for ConceptForge.

Two simple dicts keyed by id. No persistence — resets on server restart,
which is fine for the current dev/E2E scope.
"""
from __future__ import annotations

from typing import Any, Dict

# topic_id -> topic dict {id, question, background}
topics: Dict[str, dict] = {}

# submission_id -> {
#   "topic_id": str,
#   "topic": {...},
#   "submission": {guess, evidence, contradiction, revision, conclusion},
#   "evaluation": {...five dims...},
#   "alignment": {"layers": {...}, "diff": {...}},
#   "style_summary": {expression_style, thinking_traits, quality_overall, improvement},
# }
submissions: Dict[str, dict] = {}


def reset() -> None:
    """Clear all in-memory data (handy for tests)."""
    topics.clear()
    submissions.clear()


def put_topic(topic: dict) -> None:
    topics[topic["id"]] = topic


def get_topic(topic_id: str) -> Any:
    return topics.get(topic_id)


def put_submission(submission_id: str, record: dict) -> None:
    submissions[submission_id] = record


def get_submission(submission_id: str) -> Any:
    return submissions.get(submission_id)
