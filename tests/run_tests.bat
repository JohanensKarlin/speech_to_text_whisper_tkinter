@echo off
cd /d "%~dp0\.."
echo Fuehre Tests aus (Projektroot)...
python tests/run_tests.py
if errorlevel 1 exit /b 1
echo.
pause
