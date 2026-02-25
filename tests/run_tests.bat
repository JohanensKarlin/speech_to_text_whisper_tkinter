@echo off
cd /d "%~dp0\.."
echo Fuehre Tests aus (Projektroot)...
where uv >nul 2>&1
if %errorlevel% equ 0 (
  uv run python tests/run_tests.py
) else (
  python tests/run_tests.py
)
if errorlevel 1 exit /b 1
echo.
pause
