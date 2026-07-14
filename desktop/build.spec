# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for ConceptForge desktop app.

打包命令（在项目根目录运行）:
    pyinstaller desktop/build.spec

产物:
    dist/ConceptForge/          (目录模式，推荐)
    dist/ConceptForge.exe       (Windows 单文件模式可选)

平台依赖:
    Windows: 需系统装 Microsoft Edge（Win10/11 自带），用 --app 模式打开窗口
    Linux:   用默认浏览器打开
"""
from PyInstaller.utils.hooks import collect_all
import os
import sys
from pathlib import Path

block_cipher = None

# 项目根目录（即 desktop/）
ROOT = os.path.dirname(os.path.abspath(SPEC))
# 仓库根目录（desktop/..）
REPO = os.path.abspath(os.path.join(ROOT, ".."))
# backend 源码目录（backend/）
BACKEND_DIR = os.path.join(REPO, "backend")

# 把 desktop/ 和 backend/ 加入 sys.path，让 PyInstaller 分析阶段能 import 到
# desktop 和 app 包（pathex 只影响部分模块查找，sys.path 才是 import 用的）。
for p in (ROOT, BACKEND_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

# 收集 FastAPI、Uvicorn、OpenAI、httpx 的数据文件
# 注意：不再需要 webview/pythonnet/clr_loader —— 改用 Edge --app 模式打开窗口，
# 完全绕过 pywebview 的 WinForms/pythonnet 依赖链
# httpx/httpcore: openai 库的 HTTP 客户端，PyInstaller 不会自动收集
datas = []
binaries = []
for pkg in ["fastapi", "uvicorn", "openai", "pydantic", "httpx", "httpcore", "distro"]:
    d, b, _ = collect_all(pkg)
    datas += d
    binaries += b

# 加入前端构建产物（desktop/assets/）
assets_dir = os.path.join(ROOT, "assets")
if os.path.isdir(assets_dir):
    datas.append((assets_dir, "desktop/assets"))

# 把 backend/ 和 desktop/ 源码目录作为数据文件加入，作为 fallback：
# 即使 PyInstaller 漏掉某个模块的字节码，运行时也能从 .py 源码 import
# （main.py 在 frozen 模式下会把 _MEIPASS/backend 加入 sys.path）。
if os.path.isdir(BACKEND_DIR):
    datas.append((BACKEND_DIR, "backend"))
# desktop 下的 .py 文件（app.py/config.py/main.py/__init__.py）
for py in ("__init__.py", "app.py", "config.py", "build_frontend.py"):
    p = os.path.join(ROOT, py)
    if os.path.isfile(p):
        datas.append((p, "desktop"))

a = Analysis(
    ["main.py"],
    pathex=[ROOT, BACKEND_DIR],
    binaries=binaries,
    datas=datas,
    hiddenimports=[
        "httpx",
        "httpcore",
        "httpx._config",
        "httpx._models",
        "httpx._client",
        "httpx._transports",
        "httpx._transports.default",
        "httpcore._async",
        "httpcore._sync",
        "h11",
        "anyio",
        "anyio._backends",
        "anyio._backends._asyncio",
        "sniffio",
        "certifi",
        "distro",
        "uvicorn.logging",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        # desktop 包（main.py 用 desktop.config、desktop.app）
        "desktop",
        "desktop.app",
        "desktop.config",
        # app 包完整子树（显式列出，不依赖 collect_submodules —— 该函数在
        # Windows 构建机上因 sys.path 问题曾返回空列表）
        "app",
        "app.harness",
        "app.llm_client",
        "app.main",
        "app.research_pedagogy",
        "app.schemas",
        "app.store",
        "app.routers",
        "app.routers.submissions",
        "app.routers.topics",
        "app.skills",
        "app.skills.align_skill",
        "app.skills.collect_skill",
        "app.skills.evaluate_skill",
        "app.skills.style_summary_skill",
        "app.skills.topic_skill",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # frozen 模式下不使用 pywebview（走 Edge --app），排除其依赖链避免
    # 打包无用的 pythonnet/clr_loader DLL（体积大且可能引发 DLL 冲突）
    excludes=["webview", "pythonnet", "clr_loader", "clr", "System"],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ConceptForge",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX 压缩在 PyInstaller 6.x + Py 3.13 上会破坏 DLL 重定位，导致启动 ACCESS_VIOLATION
    console=True,  # 临时开 console 以便定位启动期崩溃；确认稳定后改回 False
    icon=os.path.join(ROOT, "icon.ico"),  # 应用图标
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="ConceptForge",
)
