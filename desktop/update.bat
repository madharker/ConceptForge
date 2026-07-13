@echo off
REM ConceptForge desktop updater (Windows)
REM Pulls latest code and refreshes dependencies if needed.
REM Existing .venv and assets are preserved — no full reinstall required.
setlocal
set "SCRIPT_DIR=%~dp0"
set "REPO_ROOT=%SCRIPT_DIR%.."
cd /d "%REPO_ROOT%"

if not exist "desktop\.venv\Scripts\python.exe" (
  echo 错误：未找到虚拟环境 desktop\.venv，请先运行：desktop\setup.bat
  pause
  exit /b 1
)

for /f "delims=" %%i in ('git rev-parse HEAD') do set "OLD_REV=%%i"

echo [1/3] 拉取最新代码...
git pull origin desktop
if %ERRORLEVEL% NEQ 0 (
  echo git pull 失败，请检查网络或手动解决冲突。
  pause
  exit /b 1
)

for /f "delims=" %%i in ('git rev-parse HEAD') do set "NEW_REV=%%i"

if "%OLD_REV%"=="%NEW_REV%" (
  echo 已是最新版本，无需更新。
  pause
  exit /b 0
)

echo [2/3] 检查依赖是否需要更新...
git diff --name-only "%OLD_REV%" "%NEW_REV%" | findstr /C:"desktop/requirements.txt" >nul
if %ERRORLEVEL% EQU 0 (
  echo 检测到 requirements.txt 变化，更新依赖...
  desktop\.venv\Scripts\pip.exe install -r desktop\requirements.txt
) else (
  echo 依赖未变化，跳过。
)

echo [3/3] 更新完成！运行 desktop\run.bat 启动
pause
endlocal
