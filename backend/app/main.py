"""ConceptForge FastAPI application.

CORS is permissive for the frontend dev server (allows all origins in dev,
including http://localhost:5173). Mounts the topic and submission routers.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import submissions, topics

app = FastAPI(
    title="ConceptForge 概念锻造器",
    description=(
        "研究式学习平台后端：课题生成 → 5 步研究收集 → AI 过程评定 → 主流语境对齐。"
        " 无 LLM key 时自动降级为确定性 mock，可端到端跑通。"
    ),
    version="0.1.0",
)

# Dev-friendly CORS: allow all origins (covers the Vite dev server at
# http://localhost:5173). Credentials are not used.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


app.include_router(topics.router)
app.include_router(submissions.router)
