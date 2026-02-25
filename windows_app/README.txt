Windows-App bauen und weitergeben
================================

Option A: Nur EXE weitergeben (schnell)
---------------------------------------
1. build.bat ausfuehren (Doppelklick oder: cmd, cd zum Projektordner, windows_app\build.bat)
2. Fertige Datei: dist\SpeechToText.exe
3. dist\SpeechToText.exe an deinen Freund schicken.
4. Freund: EXE in einen Ordner legen, optional config.json oder settings.json daneben fuer API-Key.
   Oder in der App unter Einstellungen API-Key eintragen (wird in settings.json gespeichert).

Option B: Installer bauen (Startmenue, Deinstaller)
--------------------------------------------------
1. Zuerst Option A (build.bat), damit dist\SpeechToText.exe existiert.
2. Inno Setup installieren: https://jrsoftware.org/isinfo.php
3. windows_app\installer.iss in Inno Setup oeffnen, Menue Build / Compile.
4. Installer liegt in windows_app\installer_output\SpeechToText_Setup.exe
5. Diesen Setup an Freund schicken; er fuehrt die Installation durch (Programme, Startmenue, optional Desktop-Icon).

Hinweis
-------
- Beim ersten Start der EXE kann Windows SmartScreen warnen ("Unbekannter Herausgeber"). 
  "Weitere Informationen" -> "Trotzdem ausfuehren" waehlen.
- API-Key: Freund kann in der App unter dem Einstellungen-Dialog den OpenAI-Key eintragen.
