# tests/ – Tests

Damit du schnell weisst: Was getestet wird, wie du die Tests ausfuehrst, und wo du neue Tests anlegst.

---

## Zweck

- **Struktur- und Modul-Tests** ohne echten API-Call und ohne Mikrofon. Pruefen, dass Config-Laden, Aufnahme-Hilfsfunktionen, WAV-Erzeugung, Prompts, Halluzinationsfilter und (optional) Fensteraufbau wie erwartet funktionieren.

---

## Ausfuehrung

- **Von Projektroot aus:**  
  `python tests/run_tests.py`  
  Wenn `sounddevice` oder `customtkinter` fehlen, werden die zugehoerigen Tests uebersprungen (SKIP). So kannst du auch ohne venv schnell Config- und Skill-Tests laufen lassen.

- **Mit venv (alle Abhaengigkeiten):**  
  `uv run python tests/run_tests.py`  
  Dann laufen alle Tests, die keine echte API und kein Mikrofon brauchen; nur der UI-Test kann z. B. bei fehlendem Display uebersprungen werden.

- **Batch (Windows):**  
  `tests/run_tests.bat` – wechselt ins Projektroot und startet `python tests/run_tests.py`.

---

## Was getestet wird (run_tests.py)

| Test | Was geprueft wird | Abhaengigkeit |
|------|--------------------|----------------|
| config load_config | Dict mit api_key; funktioniert mit vorhandenem config.json oder Temp-Datei | – |
| config settings load/save | settings.json Roundtrip (API-Key, Custom-Smoother, Modell) | – |
| ui design labels | LABEL_SPRACHE, LABEL_GLAETTEN, WINDOW_WIDTH in ui/constants.py (ohne GUI) | – |
| processing get_available_microphones | Liste von Dicts mit index/name | sounddevice |
| processing audio_to_wav | numpy -> WAV-BytesIO, lesbares RIFF-Format | sounddevice (wegen processing-Import) |
| processing record_audio (stop_event) | Mit sofort gesetztem Event liefert record_audio leeres Array | sounddevice |
| skill prompts de/en | get_prompts liefert system+user fuer de/en; unbekannte Sprache -> de | – |
| skill smooth_transcription empty | Leerer/Whitespace-Text wird unveraendert zurueckgegeben (kein API-Call) | – |
| skill smooth_transcription custom prompts | Custom-System/User-Prompts werden an API uebergeben (Mock) | – |
| transcription filter_hallucinations | hallucination.json wird geladen; Filter entfernt bekannte Phrase (en) | sounddevice (wegen processing-Import) |
| ui create_status_window | Fenster baut sich mit Dummy-Callbacks; refs befuellt; Labels Sprache/Glaetten an Schaltern | customtkinter |

Keine Tests fuer: echtes Aufnehmen, echten Whisper-Call, echte Text-Glaettung, Tastatur-Polling. Dafuer waeren Mocks oder Integrationstests noetig.

---

## Wo du ansetzt

- **Neuer Test:** In `tests/run_tests.py` eine neue Funktion `test_xyz()` schreiben und in der Liste `cases` in `run_all()` eintragen. Bei optionalen Abhaengigkeiten am Anfang der Funktion `return "skip"` wenn z. B. `not HAS_SOUNDDEVICE`.
- **Projektroot:** Die Tests setzen `sys.path` und `os.chdir` auf das Projektroot (Parent von `tests/`). Imports sind also `from config import ...`, `from processing import ...` usw. Immer aus Projektroot starten.

Wenn du nur pruefen willst, ob die Grundstruktur und die wichtigsten Funktionen laufen: `python tests/run_tests.py` reicht; mit venv siehst du die maximale Anzahl bestandener Tests.
