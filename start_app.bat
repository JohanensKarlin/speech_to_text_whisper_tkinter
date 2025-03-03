@echo off
echo Starte Sprache Zu Text Anwendung...

:: Überprüfen und Installieren der benötigten Pakete
echo Überprüfe Abhängigkeiten...

:: Verwende den vollständigen Pfad zum Python-Interpreter
"%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe" -m pip install pyautogui sounddevice keyboard pyperclip openai numpy scipy customtkinter --quiet

:: Starten der Anwendung
echo Starte Anwendung...
"%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe" speech_to_text.py
pause
