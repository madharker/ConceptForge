#!/usr/bin/env python3
"""构建桌面端前端：调用 npm install + npm run build，产物输出到 desktop/assets/。

用法:
    python desktop/build_frontend.py

前置条件:
    - Node.js 18+ 已安装
    - npm 可用
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

DESKTOP_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = DESKTOP_DIR / "frontend"
ASSETS_DIR = DESKTOP_DIR / "assets"


def run(cmd: list[str], cwd: Path, desc: str) -> None:
    print(f"==> {desc}")
    print(f"    cmd: {' '.join(cmd)}")
    print(f"    cwd: {cwd}")
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0:
        print(f"[ERROR] {desc} 失败 (exit {result.returncode})")
        sys.exit(result.returncode)
    print(f"    [OK] {desc} 完成")


def main() -> None:
    if not FRONTEND_DIR.is_dir():
        print(f"[ERROR] 前端目录不存在: {FRONTEND_DIR}")
        sys.exit(1)

    # 1. 安装依赖（若 node_modules 不存在）
    if not (FRONTEND_DIR / "node_modules").is_dir():
        run(["npm", "install"], FRONTEND_DIR, "安装前端依赖 (npm install)")
    else:
        print("==> 跳过 npm install (node_modules 已存在)")

    # 2. 构建
    run(["npm", "run", "build"], FRONTEND_DIR, "构建前端 (npm run build)")

    # 3. 确认产物
    index = ASSETS_DIR / "index.html"
    if index.exists():
        print(f"\n[DONE] 前端已构建到 {ASSETS_DIR}")
        print(f"       入口: {index}")
    else:
        print(f"\n[ERROR] 构建产物未找到: {index}")
        sys.exit(1)


if __name__ == "__main__":
    main()
