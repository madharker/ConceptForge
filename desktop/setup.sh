#!/usr/bin/env bash
# ConceptForge 桌面端一键安装脚本 (Linux / macOS)
#
# 用法:
#   bash desktop/setup.sh
#
# 功能:
#   1. 检查 Python 3.10+
#   2. 创建虚拟环境 .venv
#   3. 安装 desktop/requirements.txt
#   4. Linux: 检查 WebKitGTK 系统依赖
#   5. 检查前端构建产物 desktop/assets/
#   6. 打印启动指令
#
# 退出码: 0 成功, 非 0 失败

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${CYAN}[信息]${NC} $1"; }
ok()    { echo -e "${GREEN}[完成]${NC} $1"; }
warn()  { echo -e "${YELLOW}[警告]${NC} $1"; }
fail()  { echo -e "${RED}[错误]${NC} $1"; exit 1; }

# 定位脚本所在目录（支持软链接）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

info "ConceptForge 桌面端安装脚本"
echo "工作目录: $SCRIPT_DIR"
echo ""

# ---------- 1. 检查 Python ----------
info "检查 Python 版本..."
if command -v python3 >/dev/null 2>&1; then
    PY=python3
elif command -v python >/dev/null 2>&1; then
    PY=python
else
    fail "未找到 Python，请先安装 Python 3.10+ (https://www.python.org/downloads/)"
fi

PY_VERSION=$($PY -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$($PY -c 'import sys; print(sys.version_info.major)')
PY_MINOR=$($PY -c 'import sys; print(sys.version_info.minor)')

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
    fail "Python 版本 $PY_VERSION 过低，需要 3.10+"
fi
ok "Python $PY_VERSION"

# ---------- 2. 创建虚拟环境 ----------
VENV_DIR="$SCRIPT_DIR/.venv"
if [ -d "$VENV_DIR" ]; then
    warn "虚拟环境已存在: $VENV_DIR （将复用，如需重装请先删除该目录）"
else
    info "创建虚拟环境 .venv ..."
    $PY -m venv "$VENV_DIR"
    ok "虚拟环境创建完成"
fi

# 激活虚拟环境
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# 升级 pip
info "升级 pip ..."
$PY -m pip install --upgrade pip --quiet
ok "pip 已就绪"

# ---------- 3. 安装依赖 ----------
REQ_FILE="$SCRIPT_DIR/requirements.txt"
if [ ! -f "$REQ_FILE" ]; then
    fail "未找到 requirements.txt: $REQ_FILE"
fi

info "安装 Python 依赖 (requirements.txt) ..."
echo "  - pywebview (PyWebView 桌面框架)"
echo "  - fastapi + uvicorn (本地后端)"
echo "  - openai (LLM 客户端)"
echo "  - pydantic (数据校验)"
echo ""
pip install -r "$REQ_FILE"
ok "Python 依赖安装完成"

# ---------- 4. Linux: 检查 WebKitGTK ----------
if [ "$(uname -s)" = "Linux" ]; then
    info "检查 Linux 系统依赖 WebKitGTK ..."
    # PyWebView 在 Linux 依赖 WebKitGTK，检查 pkg-config
    if command -v pkg-config >/dev/null 2>&1; then
        if pkg-config --exists webkit2gtk-4.1 2>/dev/null; then
            ok "WebKitGTK 4.1 已安装"
        elif pkg-config --exists webkit2gtk-4.0 2>/dev/null; then
            ok "WebKitGTK 4.0 已安装"
        else
            warn "未检测到 WebKitGTK，PyWebView 启动时会报错"
            echo ""
            echo "  请用系统包管理器安装:"
            echo "    Ubuntu/Debian:  sudo apt install libwebkit2gtk-4.1-dev"
            echo "    Fedora:         sudo dnf install webkit2gtk4.1-devel"
            echo "    Arch:           sudo pacman -S webkit2gtk"
            echo ""
        fi
    else
        warn "未找到 pkg-config，无法自动检测 WebKitGTK"
        echo "  若启动时报 webview 相关错误，请安装:"
        echo "    sudo apt install libwebkit2gtk-4.1-dev"
    fi
fi

# ---------- 5. 检查前端构建产物 ----------
ASSETS_DIR="$SCRIPT_DIR/assets"
if [ -f "$ASSETS_DIR/index.html" ]; then
    ok "前端构建产物已就绪: assets/index.html"
else
    warn "未找到前端构建产物 assets/index.html"
    echo ""
    echo "  普通使用应从仓库直接获取 assets/ 目录（已预构建）。"
    echo "  如需自行重建前端（需要 Node.js):"
    echo "    python desktop/build_frontend.py"
    echo ""
fi

# ---------- 6. 完成 ----------
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ConceptForge 安装完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "启动方式:"
echo "  1. 激活虚拟环境:  source desktop/.venv/bin/activate"
echo "  2. 启动应用:      python desktop/main.py"
echo ""
echo "首次启动为 mock 模式，可直接体验完整流程。"
echo "接入真实 LLM: 启动后点击右上角「设置」填入 API 配置。"
echo ""
