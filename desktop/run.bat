@echo off
REM ConceptForge desktop launcher (Windows)
REM Double-click to run, or run from cmd: desktop\run.bat
setlocal
cd /d "%~dp0"

echo === ConceptForge Launcher ===
echo Working dir: %CD%
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found: .venv\Scripts\python.exe
    echo.
    echo Please run setup.bat first:
    echo   desktop\setup.bat
    echo.
    pause
    exit /b 1
)

echo Starting ConceptForge...
echo.
".venv\Scripts\python.exe" main.py
set EXITCODE=%ERRORLEVEL%

echo.
echo ============================================
if %EXITCODE% EQU 0 (
    echo ConceptForge exited normally.
) else (
    echo [ERROR] ConceptForge exited with code %EXITCODE%.
    echo.
    echo Common causes:
    echo   - Missing system GUI library (Linux needs WebKitGTK, see README)
    echo   - Python or dependency issue (re-run setup.bat)
    echo   - See error message above this block
)
echo ============================================
echo.
pause
endlocal
