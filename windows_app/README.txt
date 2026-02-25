Windows-App Schnellstart
-----------------------
start.bat startet die Speech-to-Text-App ohne "uv sync" (sofort starten).
Voraussetzung: Im Projektordner (eine Ebene ueber windows_app) wurde bereits
einmal "uv sync" ausgefuehrt, damit .venv existiert. Danach reicht Doppelklick
auf start.bat.

Optional: Standalone-EXE bauen
- Im Projektordner (ueber windows_app): uv add pyinstaller
- Dann: uv run pyinstaller --onefile --windowed --name SpeechToText speech_to_text.py
- EXE liegt in dist\SpeechToText.exe; kann nach windows_app kopiert werden.
- Beim Start sucht die EXE config/settings im Verzeichnis der EXE (bzw. Arbeitsverzeichnis).
