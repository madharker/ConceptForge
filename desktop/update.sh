#!/usr/bin/env bash
# ConceptForge desktop updater (Linux/macOS)
# Pulls latest code and refreshes dependencies if needed.
# Existing .venv and assets are preserved — no full reinstall required.
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

if [ ! -d "desktop/.venv" ]; then
  echo "错误：未找到虚拟环境 desktop/.venv，请先运行：bash desktop/setup.sh"
  exit 1
fi

OLD_REV="$(git rev-parse HEAD 2>/dev/null || echo "")"

echo "[1/3] 拉取最新代码..."
git pull origin desktop

NEW_REV="$(git rev-parse HEAD)"

if [ "$OLD_REV" = "$NEW_REV" ]; then
  echo "已是最新版本，无需更新。"
  exit 0
fi

echo "[2/3] 检查依赖是否需要更新..."
if git diff --name-only "$OLD_REV" "$NEW_REV" | grep -q "^desktop/requirements.txt$"; then
  echo "检测到 requirements.txt 变化，更新依赖..."
  desktop/.venv/bin/pip install -r desktop/requirements.txt
else
  echo "依赖未变化，跳过。"
fi

echo "[3/3] 更新完成！运行 bash desktop/run.sh 启动"
