"""Pydantic models for ConceptForge request/response contracts.

These mirror the spec exactly. Skills themselves operate on plain dicts;
these models validate wire input and document the response shape.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


# --- Topic -----------------------------------------------------------------

class Topic(BaseModel):
    id: str
    question: str
    background: str


class TopicRequest(BaseModel):
    subject: Optional[str] = None


# --- 5-step research submission -------------------------------------------

# Canonical field order & prompts (mirror spec exactly).
RESEARCH_FIELDS = ("guess", "evidence", "contradiction", "revision", "conclusion")
RESEARCH_PROMPTS = {
    "guess": "在查任何资料之前，你对这个课题的第一直觉是什么？",
    "evidence": "你找到了哪些信息来支持或推翻你的猜想？",
    "contradiction": "有没有哪些证据和你的猜想不一致？你怎么处理？",
    "revision": "根据新证据，你修改了哪些想法？",
    "conclusion": "用你自己的话，给出当前对这个问题最完整的解释。",
}


class ResearchSubmission(BaseModel):
    guess: str
    evidence: str
    contradiction: str
    revision: str
    conclusion: str


class SubmissionRequest(BaseModel):
    topic_id: str
    guess: str
    evidence: str
    contradiction: str
    revision: str
    conclusion: str


class SubmissionIdResponse(BaseModel):
    submission_id: str


# --- Evaluation (five dimensions) -----------------------------------------

class DimensionVerdict(BaseModel):
    verdict: str
    detail: str


class Evaluation(BaseModel):
    problem_understanding: DimensionVerdict
    evidence_quality: DimensionVerdict
    reasoning_chain: DimensionVerdict
    concept_boundary: DimensionVerdict
    contradiction_handling: DimensionVerdict


# --- Alignment (three layers + diff) --------------------------------------

class AlignmentLayers(BaseModel):
    your_expression: str
    rigorous_rewrite: str
    mainstream_definition: str


class AlignmentDiff(BaseModel):
    got_right: str
    missed: str
    gap: str
    why_limited: str


class Alignment(BaseModel):
    layers: AlignmentLayers
    diff: AlignmentDiff


# --- Composite response ----------------------------------------------------

class EvaluationResponse(BaseModel):
    topic: Topic
    submission: ResearchSubmission
    evaluation: Evaluation
    alignment: Alignment


# --- Standalone skill request bodies --------------------------------------

class EvaluateRequest(BaseModel):
    topic: Topic
    submission: ResearchSubmission


class AlignRequest(BaseModel):
    topic: Topic
    submission: ResearchSubmission
    evaluation: Optional[Evaluation] = None


# --- Style & quality summary (kept out of EvaluationResponse) --------------

class StyleSummary(BaseModel):
    expression_style: str
    thinking_traits: str
    quality_overall: str
    improvement: str


class StyleSummaryRequest(BaseModel):
    topic: Topic
    submission: ResearchSubmission
