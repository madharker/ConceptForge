"""Router: submission + standalone skill endpoints.

Business flow:
- POST /api/submissions                       -> create + evaluate + align + summarize
- GET  /api/submissions/{id}/evaluation       -> topic + submission + evaluation +
                                                 alignment (404 if missing; shape
                                                 unchanged — NO style_summary here)
- GET  /api/submissions/{id}/style-summary    -> persisted style_summary (404 if missing)

Standalone skills (each independently callable, JSON in/out):
- POST /api/skills/collect          {5 fields}                        -> normalized submission
- POST /api/skills/evaluate         {topic, submission}               -> evaluation json
- POST /api/skills/align            {topic, submission, evaluation?}  -> alignment json
- POST /api/skills/style-summary    {topic, submission}               -> style summary json
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from app import store
from app.harness import harness
from app.schemas import (
    AlignRequest,
    Alignment,
    Evaluation,
    EvaluateRequest,
    EvaluationResponse,
    ResearchSubmission,
    StyleSummary,
    StyleSummaryRequest,
    SubmissionIdResponse,
    SubmissionRequest,
    Topic,
)
from app.skills import align_skill, collect_skill, evaluate_skill, style_summary_skill
from app.skills.collect_skill import CollectValidationError

router = APIRouter()


@router.post("/api/submissions", response_model=SubmissionIdResponse)
def create_submission(body: SubmissionRequest) -> SubmissionIdResponse:
    """Accept a 5-step submission; run evaluate + align + summarize and store.

    The POST response only returns the submission id (unchanged). The
    style_summary is persisted into the record but is NOT surfaced here nor in
    GET /evaluation — it is only retrievable via /style-summary.
    """
    topic = store.get_topic(body.topic_id)
    if topic is None:
        raise HTTPException(
            status_code=404,
            detail=f"topic_id {body.topic_id!r} 不存在，请先 GET /api/topics/new。",
        )

    try:
        submission = collect_skill.collect(body.model_dump())
    except CollectValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    result = harness.evaluate_align_summarize(topic, submission)

    submission_id = f"sub-{uuid.uuid4().hex[:12]}"
    record = {
        "topic_id": body.topic_id,
        "topic": topic,
        "submission": submission,
        "evaluation": result["evaluation"],
        "alignment": result["alignment"],
        "style_summary": result["style_summary"],
    }
    store.put_submission(submission_id, record)
    return SubmissionIdResponse(submission_id=submission_id)


@router.get("/api/submissions/{sub_id}/evaluation", response_model=EvaluationResponse)
def get_evaluation(sub_id: str) -> EvaluationResponse:
    """Return topic + 5-step submission + five-dim evaluation + alignment.

    Shape is intentionally unchanged from before the style-summary feature:
    no ``style_summary`` key is present here.
    """
    record = store.get_submission(sub_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"submission {sub_id!r} 不存在。")
    return EvaluationResponse(
        topic=Topic(**record["topic"]),
        submission=ResearchSubmission(**record["submission"]),
        evaluation=Evaluation(**record["evaluation"]),
        alignment=Alignment(**record["alignment"]),
    )


@router.get("/api/submissions/{sub_id}/style-summary", response_model=StyleSummary)
def get_style_summary(sub_id: str) -> StyleSummary:
    """Return the persisted style & quality summary for a submission.

    404 if the submission record is missing OR has no style_summary.
    """
    record = store.get_submission(sub_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"submission {sub_id!r} 不存在。")
    summary = record.get("style_summary")
    if not summary:
        raise HTTPException(
            status_code=404,
            detail=f"submission {sub_id!r} 没有已生成的 style_summary。",
        )
    return StyleSummary(**summary)


# --- Standalone skill endpoints -------------------------------------------

@router.post("/api/skills/collect", response_model=ResearchSubmission)
def skill_collect(body: ResearchSubmission) -> ResearchSubmission:
    """Standalone collect skill: validate + normalize the 5 fields."""
    try:
        normalized = collect_skill.collect(body.model_dump())
    except CollectValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return ResearchSubmission(**normalized)


@router.post("/api/skills/evaluate", response_model=Evaluation)
def skill_evaluate(body: EvaluateRequest) -> Evaluation:
    """Standalone evaluate skill."""
    data = evaluate_skill.evaluate(
        body.topic.model_dump(),
        body.submission.model_dump(),
    )
    return Evaluation(**data)


@router.post("/api/skills/align", response_model=Alignment)
def skill_align(body: AlignRequest) -> Alignment:
    """Standalone align skill."""
    data = align_skill.align(
        body.topic.model_dump(),
        body.submission.model_dump(),
        body.evaluation.model_dump() if body.evaluation else None,
    )
    return Alignment(**data)


@router.post("/api/skills/style-summary", response_model=StyleSummary)
def skill_style_summary(body: StyleSummaryRequest) -> StyleSummary:
    """Standalone style & quality summary skill. Does NOT write to the store."""
    data = style_summary_skill.summarize_style(
        body.topic.model_dump(),
        body.submission.model_dump(),
    )
    return StyleSummary(**data)
