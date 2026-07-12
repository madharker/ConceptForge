@echo off
REM ============================================================
REM  ConceptForge 桌面端一键安装脚本 (Windows)
REM
REM  用法:
REM    双击运行  或  在命令行执行:  desktop\setup.bat
REM
REM  功能:
REM    1. 检查 Python 3.10+
REM    2. 创建虚拟环境 .venv
REM    3. 安装 desktop\requirements.txt
REM    4. 检查前端构建产物 desktop\assets\
REM    5. 打印启动指令
REM ============================================================

setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1

REM 切换到脚本所在目录
cd /d "%~dp0"

echo.
echo [信息] ConceptForge 桌面端安装脚本
echo [信息] 工作目录: %CD%
echo.

REM ---------- 1. 检查 Python ----------
echo [信息] 检查 Python 版本...
where python >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    echo        下载地址: https://www.python.org/downloads/
    echo        安装时请勾选 "Add Python to PATH"
    goto :fail
)

REM 读取 Python 版本
for /f "tokens=*" %%v in ('python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"') do set PY_VERSION=%%v
for /f "tokens=*" %%v in ('python -c "import sys; print(sys.version_info.major)"') do set PY_MAJOR=%%v
for /f "tokens=*" %%v in ('python -c "import sys; print(sys.version_info.minor)"') do set PY_MINOR=%%v

REM 版本检查 (需要 3.10+)
set /a PY_OK=0
if !PY_MAJOR! GTR 3 set /a PY_OK=1
if !PY_MAJOR! EQU 3 if !PY_MINOR! GEQ 10 set /a PY_OK=1

if !PY_OK! EQU 0 (
    echo [错误] Python 版本 !PY_VERSION! 过低，需要 3.10+
    goto :fail
)
echo [完成] Python !PY_VERSION!

REM ---------- 2. 创建虚拟环境 ----------
set VENV_DIR=%CD%\.venv
if exist "%VENV_DIR%" (
    echo [警告] 虚拟环境已存在: %VENV_DIR% （将复用，如需重装请先删除该目录）
) else (
    echo [信息] 创建虚拟环境 .venv ...
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [错误] 虚拟环境创建失败
        goto :fail
    )
    echo [完成] 虚拟环境创建完成
)

REM 激活虚拟环境
call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 (
    echo [错误] 虚拟环境激活失败
    goto :fail
)

REM 升级 pip
echo [信息] 升级 pip ...
python -m pip install --upgrade pip --quiet
echo [完成] pip 已就绪

REM ---------- 3. 安装依赖 ----------
set REQ_FILE=%CD%\requirements.txt
if not exist "%REQ_FILE%" (
    echo [错误] 未找到 requirements.txt: %REQ_FILE%
    goto :fail
)

echo [信息] 安装 Python 依赖 ^(requirements.txt^) ...
echo   - pywebview ^(PyWebView 桌面框架^)
echo   - fastapi + uvicorn ^(本地后端^)
echo   - openai ^(LLM 客户端^)
echo   - pydantic ^(数据校验^)
echo.
pip install -r "%REQ_FILE%"
if errorlevel 1 (
    echo [错误] 依赖安装失败
    goto :fail
)
echo [完成] Python 依赖安装完成

REM ---------- 4. 检查前端构建产物 ----------
set ASSETS_DIR=%CD%\assets
if exist "%ASSETS_DIR%\index.html" (
    echo [完成] 前端构建产物已就绪: assets\index.html
) else (
    echo [警告] 未找到前端构建产物 assets\index.html
    echo.
    echo   普通使用应从仓库直接获取 assets\ 目录（已预构建）。
    echo   如需自行重建前端（需要 Node.js^):
    echo     python desktop\build_frontend.py
    echo.
)

REM ---------- 5. 完成 ----------
echo.
echo ==================================================
echo   ConceptForge 安装完成！
echo ==================================================
echo.
echo 启动方式:
echo   1. 激活虚拟环境:  desktop\.venv\Scripts\activate
echo   2. 启动应用:      python desktop\main.py
echo.
echo 首次启动为 mock 模式，可直接体验完整流程。
echo 接入真实 LLM: 启动后点击右上角「设置」填入 API 配置。
echo.
pause
exit /b 0

:fail
echo.
echo [错误] 安装失败，请根据上方提示修复后重试。
pause
exit /b 1
