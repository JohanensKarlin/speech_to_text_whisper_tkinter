# Start Here – Kontext fuer den Assistenten (LLM)

Dieses Dokument gibt dir in wenigen Minuten genug Kontext, um im Projekt "Sprache Zu Text" zu arbeiten. Du kannst es zuerst lesen, dann bei Bedarf in die Unterordner gehen.

---

## Was die App macht

- **Spracherkennung:** Nutzer spricht, drueckt Strg+Y zum Stoppen. Audio wird an OpenAI Whisper geschickt, Transkript zurueckgegeben.
- **Nachbearbeitung:** Optional Halluzinationsfilter (hallucination.json) und Text-Glaettung (GPT, sprachabhaengig DE/EN).
- **Einfuegen:** Ergebnis wird in Zwischenablage kopiert und per Strg+V eingefuegt (aktivem Fenster).
- **UI:** Schwebendes Fenster (CustomTkinter): Sprache DE/EN, Switch fuer Text-Glaettung, Minimal-/Normal-Modus, Start/Stop/Mikrofon, Tastatur an/aus, Einstellungen, Beenden. In Einstellungen: API-Key ablegen, Custom-Prompts fuer Text-Glaettung (sonst Default DE/EN).

---

## Wo was liegt (Landkarte)

| Bereich | Ordner/Datei | Wann du dort nachschaust |
|--------|----------------|---------------------------|
| Einstieg, State, Callbacks, Tastatur, Mainloop | `speech_to_text.py` | Aenderungen an Ablauf, Hotkeys, neuen Buttons/Callbacks |
| Konfiguration (API-Key, spaeter mehr) | `config/` | Neue Config-Keys, anderes Config-Format |
| Aufnahme + Transkription (Whisper, Filter, Glaettung) | `processing/` | Mikrofon, WAV, OpenAI-Transkription, Halluzinationen |
| Fenster, Animation, Drag | `ui/` | Layout, neue UI-Elemente, Animation |
| Text-Glaettung (GPT-Prompts DE/EN) | `skill/text_smoothing/` | Prompts aendern, weitere Sprachen, anderes Modell |
| Tests | `tests/` | Tests ausfuehren, neue Tests hinzufuegen |

Datenfluss in einem Satz: **speech_to_text** holt Config, baut State + Callbacks, erstellt ueber **ui** das Fenster; bei Start-Aufnahme laeuft **processing.recording** (bis Stop-Event), dann **processing.transcription** (Whisper, Filter, optional **skill.text_smoothing**); Ergebnis wird eingefuegt.

---

## Wichtige Konzepte (damit du sie sofort erkennst)

- **State** (`speech_to_text.py`, Dict `state`): Einzige zentrale Daten: Sprache, Mikrofon-Index, Glaettung an/aus, Minimal-Modus, Tastatur an/aus, Aufnahme-Flag, Stop-Event. Callbacks und `process_recording` lesen/schreiben hier.
- **refs** (von `create_status_window` befuellt): Referenzen auf Fenster und Widgets (z. B. `window`, `lang_label`, `transform_text_var`). Callbacks nutzen refs, um die Anzeige zu aktualisieren (Label, Button-Text, Frames ein-/ausblenden).
- **Callbacks:** Die UI ruft nur Funktionen auf, die in `speech_to_text.py` definiert sind. Keine App-Logik in `ui/` – nur Aufbau und Aufruf der Callbacks.
- **Stop der Aufnahme:** Ein `threading.Event`. Main-Thread setzt es bei Strg+Y oder Stop-Button; `record_audio` in einem Daemon-Thread bricht ab, wenn das Event gesetzt ist.

---

## Naechste Schritte fuer dich

1. **Struktur verstehen:** [docs/config/README.md](config/README.md), [docs/processing/README.md](processing/README.md), [docs/ui/README.md](ui/README.md), [docs/skill/README.md](skill/README.md), [docs/tests/README.md](tests/README.md) – je ein kurzes Doc pro Bereich.
2. **App starten:** Von Projektroot `uv run python speech_to_text.py` oder `start_app.bat`. API-Key: in `config.json` oder ueber Einstellungen (wird in `settings.json` gespeichert, ueberschreibt config).
3. **Tests:** `python tests/run_tests.py` (von Projektroot); mit venv: `uv run python tests/run_tests.py`. Siehe [docs/tests/README.md](tests/README.md).

Refactor-Entscheidung: Die aktuelle Aufteilung (Einstieg, config, processing, ui, skill) reicht aus. Zusaetzlicher Refactor ist nur sinnvoll, wenn konkrete Probleme auftauchen (z. B. ein Modul wird zu gross oder du willst eine zweite UI).
