"""Router: topic endpoints.

- GET  /api/topics/new?subject=<optional>
- POST /api/skills/topic   {subject?} -> topic json
"""
from __future__ import annotations

from fastapi import APIRouter

from app.harness import harness
from app.schemas import Topic, TopicRequest

router = APIRouter()


@router.get("/api/topics/new", response_model=Topic)
def new_topic(subject: str | None = None) -> Topic:
    """Generate a new research topic (question form + background)."""
    topic = harness.new_topic(subject)
    return Topic(**topic)


@router.post("/api/skills/topic", response_model=Topic)
def skill_topic(body: TopicRequest) -> Topic:
    """Standalone topic skill invocation."""
    topic = harness.new_topic(body.subject)
    return Topic(**topic)
