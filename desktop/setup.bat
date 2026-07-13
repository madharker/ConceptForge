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
REM Strategy: bypass PATH (Store stub may shadow real Python).
REM   1. Try `py -3` launcher with a real script test (-c, not --version)
REM   2. Try scanning common install locations for python.exe directly
REM   3. Try `python` from PATH as last resort
echo [1/4] Checking Python...

set PY_CMD=

REM 1a. Try py launcher (tests with -c, not --version, to reject Store stubs)
py -3 -c "import sys" >nul 2>&1
if not errorlevel 1 (
    set PY_CMD=py -3
    goto :found_python
)

REM 1b. Scan common install locations (bypasses PATH/Store stub entirely)
REM     python.org default user install: %LOCALAPPDATA%\Programs\Python\Python3xx\
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
    if exist "%%D\python.exe" (
        "%%D\python.exe" -c "import sys" >nul 2>&1
        if not errorlevel 1 (
            set PY_CMD="%%D\python.exe"
            goto :found_python
        )
    )
)
REM     All-users install: C:\Program Files\Python3xx\
for /d %%D in ("C:\Program Files\Python\Python3*") do (
    if exist "%%D\python.exe" (
        "%%D\python.exe" -c "import sys" >nul 2>&1
        if not errorlevel 1 (
            set PY_CMD="%%D\python.exe"
            goto :found_python
        )
    )
)
REM     Legacy install: C:\Python3xx\
for /d %%D in ("C:\Python3*") do (
    if exist "%%D\python.exe" (
        "%%D\python.exe" -c "import sys" >nul 2>&1
        if not errorlevel 1 (
            set PY_CMD="%%D\python.exe"
            goto :found_python
        )
    )
)

REM 1c. Last resort: `python` from PATH (may be Store stub, test with -c)
python -c "import sys" >nul 2>&1
if not errorlevel 1 (
    set PY_CMD=python
    goto :found_python
)

REM Nothing worked
echo.
echo [ERROR] Could not find a working Python 3.10+ on this system.
echo.
echo The `python` command on this PC is likely the Microsoft Store stub,
echo which cannot run scripts. A real Python install is required.
echo.
echo Please install Python 3.10+ ^(64-bit^) from this direct link:
echo   https://www.python.org/ftp/python/3.13.14/python-3.13.14-amd64.exe
echo.
echo During installation:
echo   1. Check "Add Python to PATH" ^(bottom of installer window^)
echo   2. Click "Install Now"
echo   3. Let it finish completely
echo.
echo After install, CLOSE this window and re-run setup.bat.
echo This script scans install locations directly, so even if PATH is
echo not set, it should find Python automatically.
echo.
pause
    exit /b 1

:found_python
REM Write version to temp file (avoids for/f parsing issues with python output)
REM Note: %%d in batch => %d passed to Python (cmd.exe eats single %)
!PY_CMD! -c "import sys; open('_pyver.txt','w').write('%%d.%%d' %% (sys.version_info.major, sys.version_info.minor))"
if errorlevel 1 (
    echo.
    echo [ERROR] Python was found but cannot execute scripts.
    echo This should not happen - please report this issue.
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
echo       - fastapi, uvicorn, openai, pydantic, httpx
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
