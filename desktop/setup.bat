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
echo [1/4] Checking Python...
where python >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] Python not found.
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo Be sure to check "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)

REM Parse version via file to avoid cmd parsing issues with python output
python -c "import sys; open('_pyver.txt','w').write('%d.%d' % (sys.version_info.major, sys.version_info.minor))" >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] Python exists but failed to run. Possible PATH or install issue.
    echo.
    pause
    exit /b 1
)
set /p PY_VER=<_pyver.txt
del _pyver.txt >nul 2>&1

REM Extract major.minor as integers
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
echo       Python !PY_VER! OK

REM ---------- 2. Create venv ----------
echo [2/4] Creating virtual environment .venv...
if exist ".venv\Scripts\python.exe" (
    echo       .venv already exists, reusing.
) else (
    python -m venv .venv
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

".venv\Scripts\pip.exe" install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERROR] Dependency install failed.
    echo Common fixes:
    echo   - Check internet connection
    echo   - Try a different PyPI mirror: pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
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
