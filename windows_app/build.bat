@echo off
cd /d "%~dp0\.."
set "ROOT=%CD%"
set BUILD_OK=1

where uv >nul 2>&1
if %errorlevel% equ 0 (
  echo Build starten...
  uv run pyinstaller --noconfirm --clean "windows_app\speech_to_text.spec"
  if errorlevel 1 (
    echo Fehler: PyInstaller fehlgeschlagen.
    set BUILD_OK=1
    goto :ende
  )
  set BUILD_OK=0
) else (
  set PY=python
  if exist ".venv\Scripts\python.exe" set PY=.venv\Scripts\python.exe
  echo PyInstaller installieren...
  "%PY%" -m pip install pyinstaller --quiet
  if errorlevel 1 (
    echo Fehler: pip nicht verfuegbar. Tipp: uv installieren.
    goto :ende
  )
  echo Build starten...
  "%PY%" -m PyInstaller --noconfirm --clean "windows_app\speech_to_text.spec"
  set BUILD_OK=%errorlevel%
)

if %BUILD_OK% neq 0 (
  echo Fehler: PyInstaller fehlgeschlagen.
  goto :ende
)

echo.
echo Fertig. EXE: %ROOT%\dist\SpeechToText.exe
echo Zum Verteilen: EXE schicken, Empfaenger Doppelklick, in der App API-Key eintragen.

:ende
pause
