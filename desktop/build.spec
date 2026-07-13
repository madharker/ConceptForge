# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for ConceptForge desktop app.

打包命令（在项目根目录运行）:
    pyinstaller desktop/build.spec

产物:
    dist/ConceptForge/          (目录模式，推荐)
    dist/ConceptForge.exe       (Windows 单文件模式可选)

平台依赖:
    Windows: 无额外系统依赖（PyWebView 用 Edge WebView2，Win10+ 自带）
    Linux:   需系统装 WebKitGTK (apt install libwebkit2gtk-4.1-dev)
"""
from PyInstaller.utils.hooks import collect_all, collect_data_files
import os
from pathlib import Path

block_cipher = None

# 项目根目录
ROOT = os.path.dirname(os.path.abspath(SPEC))

# 收集 PyWebView、FastAPI、Uvicorn、OpenAI 的数据文件
datas = []
binaries = []
for pkg in ["webview", "fastapi", "uvicorn", "openai", "pydantic"]:
    d, b, _ = collect_all(pkg)
    datas += d
    binaries += b

# 加入前端构建产物（desktop/assets/）
assets_dir = os.path.join(ROOT, "assets")
if os.path.isdir(assets_dir):
    datas.append((assets_dir, "desktop/assets"))

# 加入 backend 源码（skills/harness 等 Python 模块，PyInstaller 会自动追踪，
# 但为确保 app.routers 等子包完整打包，显式加入）
# ROOT = desktop/，backend 在仓库根，即 desktop/../backend
backend_dir = os.path.join(ROOT, "..", "backend")
if os.path.isdir(backend_dir):
    datas.append((backend_dir, "backend"))

a = Analysis(
    ["main.py"],
    pathex=[ROOT, os.path.join(ROOT, "..", "backend")],
    binaries=binaries,
    datas=datas,
    hiddenimports=[
        "uvicorn.logging",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "app.routers.topics",
        "app.routers.submissions",
        "app.skills.topic_skill",
        "app.skills.collect_skill",
        "app.skills.evaluate_skill",
        "app.skills.align_skill",
        "app.skills.style_summary_skill",
        "desktop.app",
        "desktop.config",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    upx=True,
    console=False,  # 无控制台窗口（GUI 应用）
    icon=os.path.join(ROOT, "icon.ico"),  # 应用图标（铁砧+火焰）
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="ConceptForge",
)
