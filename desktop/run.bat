@echo off
REM ConceptForge desktop launcher (Windows)
REM Auto-uses the project venv python, no manual activation needed.
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo 错误：未找到虚拟环境 .venv，请先运行：setup.bat
  pause
  exit /b 1
)

".venv\Scripts\python.exe" main.py %*
if %ERRORLEVEL% NEQ 0 (
  echo.
  echo 程序异常退出，代码 %ERRORLEVEL%
  pause
)
endlocal
