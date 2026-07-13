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
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules
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

# 关键：把 desktop/ 和 backend/ 加入 sys.path，否则 collect_submodules('app')
# 在 Windows 构建机上返回空列表（找不到 app 包），导致 frozen exe 运行时
# 报 ModuleNotFoundError: No module named 'app'。
# pathex 只影响 PyInstaller 分析阶段的模块查找，不影响 collect_submodules。
for p in (ROOT, BACKEND_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

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

# 显式收集 desktop 和 app 包的数据文件（.py 之外的资源）
datas += collect_data_files("desktop")
datas += collect_data_files("app")

# 枚举两个包的完整子模块列表（必须在 sys.path 修复之后调用）
_app_subs = collect_submodules("app")
_desktop_subs = collect_submodules("desktop")
print(f"[spec] app submodules: {_app_subs}")
print(f"[spec] desktop submodules: {_desktop_subs}")

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
        # desktop 包完整子树
        *_desktop_subs,
        # app 包完整子树（harness/store/schemas 等被动态导入）
        *_app_subs,
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
