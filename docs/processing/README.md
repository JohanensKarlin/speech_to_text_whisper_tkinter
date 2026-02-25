# processing/ – Aufnahme und Transkription

Damit du schnell weisst: Wo Aufnahme und Transkription passieren, wer was aufruft, und wo du eingreifst.

---

## Zweck

- **Aufnahme:** Mikrofon-Stream lesen bis ein externes Stop-Event gesetzt wird; Audio als numpy-Array und als WAV (BytesIO) bereitstellen.
- **Transkription:** WAV an OpenAI Whisper senden, Rohtext zurueckbekommen, Halluzinationsfilter anwenden, optional Text-Glaettung (Skill) aufrufen.

Kein UI, keine Tastatur-Logik – nur Daten und API-Calls. Start/Stop der Animation und Einfuegen des Textes macht der Aufrufer (`speech_to_text.process_recording`).

---

## Module

### recording.py

- **get_available_microphones()**  
  Liefert Liste `[{"index": int, "name": str}, ...]` fuer alle Eingabegerate (sounddevice). Wird fuer den Mikrofon-Dialog und beim Start genutzt.

- **record_audio(device_index, stop_event, sample_rate=44100)**  
  Blockiert bis `stop_event.is_set()`. Liest in 1-Sekunden-Chunks. Wird aus einem Daemon-Thread aufgerufen; der Main-Thread setzt `stop_event` bei Strg+Y oder Stop-Button.  
  Return: `np.ndarray` (int16, mono) oder leeres Array.

- **audio_to_wav(audio_data, sample_rate=44100)**  
  Nimmt das numpy-Array und gibt ein `io.BytesIO` mit WAV-Inhalt zurueck (Position 0), z. B. fuer die OpenAI-API.

### transcription.py

- **transcribe(client, audio_file, language, hallucination_path, transform_enabled, model_transcribe=...)**  
  - Schreibt WAV in eine Temp-Datei, ruft `client.audio.transcriptions.create(...)` auf, loescht die Temp-Datei.  
  - Laedt `hallucination.json` ueber `_load_hallucinations`, wendet `_filter_hallucinations` an (Regex-Entfernung bekannter Phrasen pro Sprache).  
  - Wenn `transform_enabled`: ruft `skill.text_smoothing.smooth_transcription(client, text, language)` auf.  
  - Return: fertiger Text oder `None` bei Fehler.

- **Hilfsfunktionen (intern):**  
  - `_load_hallucinations(path)` – JSON als Dict.  
  - `_filter_hallucinations(text, lang_key, hallucinations)` – entfernt Muster der gewaehlten Sprache, bereinigt Leerzeichen.

---

## Datenfluss (fuer dich zum Einordnen)

1. `speech_to_text.process_recording` startet Animation, ruft `record_audio(selected_mic_index, stop_recording_event)` auf.
2. Nach Ende: `audio_to_wav(audio_data)` -> BytesIO.
3. `transcribe(client, wav_file, language, path_to_hallucination.json, transform_enabled)` -> Text.
4. Aufrufer kopiert Text in Zwischenablage und fuegt ein.

---

## Wo du ansetzt

- **Anderes Mikrofon-Format / andere Abfrage:** `get_available_microphones` anpassen.
- **Sample-Rate, Chunk-Groesse:** Parameter in `record_audio` / `audio_to_wav`.
- **Whisper-Modell, Parameter:** `transcribe(..., model_transcribe=...)` und API-Call in `transcription.py`.
- **Halluzinationen:** `hallucination.json` im Projektroot bearbeiten (Sprachen als Keys, Listen von Phrasen). Logik in `_filter_hallucinations`.
- **Nachbearbeitung vor oder nach Glaettung:** In `transcription.transcribe` die Reihenfolge oder zusaetzliche Schritte einbauen; Text-Glaettung bleibt im Skill.
