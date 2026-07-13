#!/usr/bin/env bash
# ConceptForge desktop launcher (Linux/macOS)
# Auto-uses the project venv python, no manual activation needed.
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

if [ ! -d ".venv" ]; then
  echo "错误：未找到虚拟环境 .venv，请先运行：bash setup.sh"
  exit 1
fi

PYTHON=".venv/bin/python"
if [ ! -x "$PYTHON" ]; then
  echo "错误：venv python 不存在：$PYTHON"
  exit 1
fi

exec "$PYTHON" main.py "$@"
