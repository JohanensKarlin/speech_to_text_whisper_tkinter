# Projektstruktur

Einstieg: `speech_to_text.py` (State, Callbacks, Mainloop). UI und Processing ausgelagert.
Alle Module sind mit Kommentaren versehen (Zweck, Ablauf, Schnittstellen) fuer Weiterarbeit mit LLM.

**Dokumentation fuer den Assistenten (LLM):** [docs/start_here.md](docs/start_here.md) – Einstieg; dann docs/config, docs/processing, docs/ui, docs/skill, docs/tests.

```
Sprache Zu Text/
  speech_to_text.py     # Einstieg: config, state, callbacks, Tastatur-Poll, mainloop
  config/
    load.py             # load_config(dir) -> api_key etc.
  processing/
    recording.py        # record_audio(device, stop_event), audio_to_wav(), get_available_microphones()
    transcription.py    # transcribe(client, wav, language, hallucination_path, transform_enabled)
  ui/
    window.py           # create_status_window(callbacks, hotkeys, initial_state, refs)
    animation.py        # init_animation(), start/stop_wave_animation(), start_reverse_animation()
  skill/
    text_smoothing/     # smooth_transcription(client, text, language) – Prompts DE/EN
```

App aus Projektroot starten (z.B. `uv run python speech_to_text.py` oder venv + `python speech_to_text.py`).

Tests: `python tests/run_tests.py` (von Projektroot). Bei fehlenden Abhaengigkeiten werden Tests uebersprungen (SKIP). Volle Suite mit venv: `uv run python tests/run_tests.py` oder `tests/run_tests.bat`.
