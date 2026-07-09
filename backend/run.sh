#!/usr/bin/env bash
# ConceptForge backend launcher.
# Runs the FastAPI app via uvicorn on 0.0.0.0:8000.
set -euo pipefail

cd "$(dirname "$0")"

export PORT="${PORT:-8000}"
export HOST="${HOST:-0.0.0.0}"

exec uvicorn app.main:app --host "$HOST" --port "$PORT"
