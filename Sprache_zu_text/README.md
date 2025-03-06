# Sprache Zu Text - Spracherkennung und Transkription

## Projektübersicht
Eine Python-basierte Spracherkennungsanwendung mit minimalistischer, schwebender Benutzeroberfläche zur Transkription von Audio in Deutsch und Englisch.

## Kernfunktionalität
- Aufnahme von Audio über das Mikrofon
- Transkription von Audio mit OpenAIs Whisper API
- Automatisches Einfügen der Transkription an der Cursorposition
- Unterstützung für mehrere Sprachen (Deutsch und Englisch)

## Technischer Stack
- Python 3.10+
- Bibliotheken:
  - sounddevice (Audioaufnahme)
  - tkinter (GUI)
  - keyboard (globale Tastenkombinationen)
  - pyautogui (Texteinfügung)
  - pyperclip (Zwischenablage-Management)
  - OpenAI (Transkription)

## Benutzeroberfläche
- Kompaktes, rahmenloses Fenster mit abgerundeten Ecken
- Dunkelgraues Farbschema (#424242)
- Ziehbare Oberfläche
- Immer-im-Vordergrund-Verhalten
- Abgerundete Buttons mit subtilen Hover-Effekten
- Einheitliche hellgraue Farbe (#9E9E9E)
- Mute-Button ändert sich zu dunkelgrau (#666666), wenn Tastenkombinationen deaktiviert sind
- Wellenanimation während der Aufnahme (links nach rechts)
- Umgekehrte Wellenanimation während der Transkription (rechts nach links)

## Tastenkombinationen
- Strg+A: Aufnahme starten
- Strg+S: Aufnahme stoppen
- Alt+L: Sprache umschalten
- Alt+M: Tastenkombinationen aktivieren/deaktivieren
- Alt+Q: Anwendung beenden

## Sprachverwaltung
- Umschalten zwischen Deutsch und Englisch
- Sprachauswahl über Button
- OpenAI Whisper API verarbeitet die Transkriptionssprache

## Anwendung starten

### Methode 1: Batch-Datei (mit Konsolenfenster)
Doppelklicken Sie auf `start_app.bat`, um die Anwendung zu starten. Diese Datei:
- Installiert automatisch alle benötigten Abhängigkeiten
- Startet die Anwendung mit einem sichtbaren Konsolenfenster

### Methode 2: VBS-Skript (ohne Konsolenfenster)
Doppelklicken Sie auf `start_app_hidden.vbs`, um die Anwendung ohne Konsolenfenster zu starten.

### Methode 3: Ausführbare Datei (.exe)
Eine eigenständige ausführbare Datei kann mit PyInstaller erstellt werden:

```bash
# Installieren der neuesten Hooks
pip install -U pyinstaller-hooks-contrib

# Erstellen der ausführbaren Datei
pyinstaller --onefile --windowed --recursive-copy-metadata openai --recursive-copy-metadata tqdm --hidden-import=openai --hidden-import=tqdm --name="SpracheZuText" speech_to_text.py
```

Die ausführbare Datei wird im Ordner `dist` erstellt und kann auf jeden Windows-Computer kopiert und ausgeführt werden, ohne dass Python installiert sein muss.

## Autostart einrichten
1. Drücken Sie `Win+R`, geben Sie `shell:startup` ein und drücken Sie Enter
2. Kopieren Sie `start_app_hidden.vbs` oder eine Verknüpfung zur .exe-Datei in diesen Ordner

## Bekannte Probleme und Lösungen
- **OpenAI-Modul-Fehler bei .exe**: Verwenden Sie die oben genannten PyInstaller-Optionen, um Metadaten und versteckte Abhängigkeiten einzuschließen
- **Fenster springt beim Klicken**: Behoben durch verbesserte Drag-Funktionalität
- **Mehrfache Mute-Button-Aktivierung**: Behoben durch Verzögerung zwischen Klicks

## Sicherheitshinweise
- Der OpenAI API-Schlüssel ist derzeit im Code hartcodiert
- Für Produktionsumgebungen sollte der API-Schlüssel in Umgebungsvariablen oder einer sicheren Konfigurationsdatei gespeichert werden

## Zukünftige Verbesserungen
1. Konfigurationsdatei-Unterstützung
2. Protokollierungsmechanismus
3. Installer/Paketierungsskript
4. Umfassende Unit- und Integrationstests
5. Weitere Sprachoptionen
6. Benutzerdefinierte Tastenkombinationen
7. Benutzerdefinierte UI-Themes
8. Detailliertere Aufnahmesteuerung
9. Verbesserte Fehlerbehandlung
10. Leistungsoptimierungen
