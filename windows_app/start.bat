@echo off
cd /d "%~dp0\.."

if exist ".venv\Scripts\pythonw.exe" (
  start "" ".venv\Scripts\pythonw.exe" speech_to_text.py
) else (
  where pythonw >nul 2>&1
  if errorlevel 1 (
    echo pythonw nicht gefunden. Bitte Python installieren oder im Projektordner: uv sync
    pause
    exit /b 1
  )
  start "" pythonw speech_to_text.py
)
