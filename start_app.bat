@echo off
cd /d "%~dp0"

:: uv: Sync venv and run app without console window
where uv >nul 2>&1
if errorlevel 1 (
  echo uv not found. Install: pip install uv  or  winget install uv
  pause
  exit /b 1
)

uv sync
if errorlevel 1 (
  pause
  exit /b 1
)

:: Start without console (pythonw in venv)
if exist ".venv\Scripts\pythonw.exe" (
  start "" ".venv\Scripts\pythonw.exe" speech_to_text.py
) else (
  start "" uv run speech_to_text.py
)
