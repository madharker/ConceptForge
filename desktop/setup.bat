@echo off
REM ============================================================
REM  ConceptForge desktop setup (Windows)
REM  Double-click to run, or run from cmd: desktop\setup.bat
REM ============================================================
setlocal EnableDelayedExpansion
cd /d "%~dp0"

echo.
echo === ConceptForge Setup ===
echo Working dir: %CD%
echo.

REM ---------- 1. Check Python ----------
REM Prefer `py -3` (official launcher, always works if Python installed).
REM Fall back to `python` (may be Windows Store stub - will fail below).
echo [1/4] Checking Python...

set PY_CMD=
py -3 --version >nul 2>&1
if not errorlevel 1 (
    set PY_CMD=py -3
) else (
    python --version >nul 2>&1
    if not errorlevel 1 (
        set PY_CMD=python
    )
)

if "!PY_CMD!"=="" (
    echo.
    echo [ERROR] Python is not installed on this system.
    echo.
    echo Please download and install Python 3.10+ ^(64-bit^):
    echo   https://www.python.org/ftp/python/3.13.14/python-3.13.14-amd64.exe
    echo.
    echo During installation, you MUST:
    echo   1. Check "Add Python to PATH" ^(bottom of installer window^)
    echo   2. Click "Install Now"
    echo.
    echo After install, CLOSE this window and re-run setup.bat.
    echo Do NOT use Microsoft Store version - it will not work.
    echo.
    pause
    exit /b 1
)

REM Write version to temp file (avoids for/f parsing issues with python output)
!PY_CMD! -c "import sys; open('_pyver.txt','w').write('%d.%d' % (sys.version_info.major, sys.version_info.minor))"
if errorlevel 1 (
    echo.
    echo [ERROR] Python was found but cannot execute scripts.
    echo.
    echo This is likely the Microsoft Store Python stub, which does not work.
    echo.
    echo Fix: Install real Python from the direct link below:
    echo   https://www.python.org/ftp/python/3.13.14/python-3.13.14-amd64.exe
    echo.
    echo During install, check "Add Python to PATH" then "Install Now".
    echo After install, close this window and re-run setup.bat.
    echo.
    pause
    exit /b 1
)
set /p PY_VER=<_pyver.txt
del _pyver.txt >nul 2>&1

for /f "tokens=1,2 delims=." %%a in ("%PY_VER%") do (
    set PY_MAJOR=%%a
    set PY_MINOR=%%b
)

set PY_OK=0
if !PY_MAJOR! GTR 3 set PY_OK=1
if !PY_MAJOR! EQU 3 if !PY_MINOR! GEQ 10 set PY_OK=1

if !PY_OK! EQU 0 (
    echo.
    echo [ERROR] Python !PY_VER! is too old. Need 3.10+.
    echo.
    pause
    exit /b 1
)
echo       Using: !PY_CMD! ^(!PY_VER!^)

REM ---------- 2. Create venv ----------
echo [2/4] Creating virtual environment .venv...
if exist ".venv\Scripts\python.exe" (
    echo       .venv already exists, reusing.
) else (
    !PY_CMD! -m venv .venv
    if errorlevel 1 (
        echo.
        echo [ERROR] venv creation failed.
        echo.
        pause
        exit /b 1
    )
)
echo       venv ready

REM ---------- 3. Install deps ----------
echo [3/4] Installing dependencies (may take a few minutes)...
echo       - pywebview, fastapi, uvicorn, openai, pydantic
echo.

".venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
if errorlevel 1 (
    echo [WARN] pip upgrade failed, continuing with current pip...
)

if not exist "requirements.txt" (
    echo.
    echo [ERROR] requirements.txt not found in %CD%
    echo.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERROR] Dependency install failed.
    echo Common fixes:
    echo   - Check internet connection
    echo   - Try a PyPI mirror (China):
    echo     ".venv\Scripts\python.exe" -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    echo.
    pause
    exit /b 1
)
echo       Dependencies installed

REM ---------- 4. Check frontend assets ----------
echo [4/4] Checking frontend assets...
if exist "assets\index.html" (
    echo       assets\index.html ready
) else (
    echo.
    echo [WARN] assets\index.html not found.
    echo   Normal users should get it from the repo. To rebuild (needs Node.js):
    echo     python build_frontend.py
    echo.
)

REM ---------- Done ----------
echo.
echo ============================================
echo   Setup complete!
echo ============================================
echo.
echo To start ConceptForge:
echo   Double-click run.bat
echo   or run: desktop\run.bat
echo.
echo First launch runs in mock mode (no API key needed).
echo To use a real LLM, click Settings in the app after launch.
echo.
pause
exit /b 0
