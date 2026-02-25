# =============================================================================
# tests/run_tests.py – Struktur- und Modul-Tests (ohne API/Mikrofon)
# =============================================================================
# Von Projektroot aus starten: python tests/run_tests.py
# Prueft: config, processing (recording, transcription Filter), skill (prompts),
# optional UI-Import. Kein echter API-Call, kein Mikrofon.
# =============================================================================

import importlib.util
import os
import sys
import tempfile
import threading

# Projektroot = Parent von tests/
APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, APP_ROOT)
os.chdir(APP_ROOT)

# Optionale Abhaengigkeiten (wenn nicht installiert: Tests ueberspringen)
try:
    import sounddevice
    HAS_SOUNDDEVICE = True
except ImportError:
    HAS_SOUNDDEVICE = False
try:
    import customtkinter
    HAS_CTK = True
except ImportError:
    HAS_CTK = False

def test_config_load():
    """Config aus vorhandenem config.json oder Temp-Datei; fehlt Datei -> leeres Dict."""
    from config import load_config
    with tempfile.TemporaryDirectory() as d:
        cfg = load_config(d)
        assert isinstance(cfg, dict) and len(cfg) == 0, "Ohne config.json: leeres Dict"
        with open(os.path.join(d, "config.json"), "w", encoding="utf-8") as f:
            f.write('{"api_key": "test-key"}')
        cfg = load_config(d)
        assert cfg.get("api_key") == "test-key"
    return True

def test_get_available_microphones():
    """Mikrofon-Liste: Liste von Dicts mit index und name."""
    if not HAS_SOUNDDEVICE:
        return "skip"
    from processing import get_available_microphones
    mics = get_available_microphones()
    assert isinstance(mics, list), "Mikrofone muessen Liste sein"
    for m in mics:
        assert "index" in m and "name" in m
    return True

def test_audio_to_wav():
    """audio_to_wav erzeugt lesbares WAV aus numpy-Array."""
    if not HAS_SOUNDDEVICE:
        return "skip"
    import numpy as np
    from processing import audio_to_wav
    # 1 Sekunde Stille (44100 Samples)
    data = np.zeros(44100, dtype=np.int16)
    wav = audio_to_wav(data)
    assert wav is not None
    raw = wav.read()
    assert len(raw) >= 44, "WAV-Header + Daten"
    assert raw[:4] == b"RIFF", "WAV-Format"
    wav.seek(0)
    return True

def test_record_audio_stop_event():
    """record_audio bricht sofort ab wenn stop_event gesetzt."""
    if not HAS_SOUNDDEVICE:
        return "skip"
    from processing import record_audio
    ev = threading.Event()
    ev.set()
    out = record_audio(0, ev, sample_rate=44100)
    assert out is not None
    assert hasattr(out, "size")
    assert out.size == 0, "Sofort gestoppt = leeres Array"
    return True

def test_prompts_de_en():
    """Skill prompts: de und en liefern system + user."""
    from skill.text_smoothing.prompts import get_prompts
    for lang in ("de", "en"):
        p = get_prompts(lang)
        assert "system" in p and "user" in p
        assert len(p["system"]) > 0 and len(p["user"]) > 0
    # Unbekannte Sprache -> Fallback DE
    p = get_prompts("xy")
    assert "system" in p
    return True

def test_smooth_transcription_empty():
    """smooth_transcription bei leerem Text gibt Text unveraendert zurueck."""
    from skill.text_smoothing import smooth_transcription
    class FakeClient:
        pass
    assert smooth_transcription(FakeClient(), "", "de") == ""
    assert smooth_transcription(FakeClient(), "  ", "en") == "  "
    return True

def test_settings_load_save():
    """Settings: load_settings/save_settings roundtrip in Temp-Dir (inkl. smoother_model)."""
    from config import load_settings, save_settings, KEY_API_KEY, KEY_USE_CUSTOM_SMOOTHER, KEY_CUSTOM_SMOOTHER_SYSTEM, KEY_CUSTOM_SMOOTHER_USER, KEY_SMOOTHER_MODEL, DEFAULT_SMOOTHER_MODEL
    with tempfile.TemporaryDirectory() as d:
        empty = load_settings(d)
        assert empty == {} or (isinstance(empty, dict) and KEY_API_KEY in empty)
        save_settings(d, {
            KEY_API_KEY: "sk-test",
            KEY_USE_CUSTOM_SMOOTHER: True,
            KEY_CUSTOM_SMOOTHER_SYSTEM: "System",
            KEY_CUSTOM_SMOOTHER_USER: "User",
            KEY_SMOOTHER_MODEL: "gpt-4o",
        })
        loaded = load_settings(d)
        assert loaded.get(KEY_API_KEY) == "sk-test"
        assert loaded.get(KEY_USE_CUSTOM_SMOOTHER) is True
        assert loaded.get(KEY_CUSTOM_SMOOTHER_SYSTEM) == "System"
        assert loaded.get(KEY_CUSTOM_SMOOTHER_USER) == "User"
        assert loaded.get(KEY_SMOOTHER_MODEL) == "gpt-4o"
        save_settings(d, {})
        loaded2 = load_settings(d)
        assert loaded2.get(KEY_SMOOTHER_MODEL) == DEFAULT_SMOOTHER_MODEL
    return True

def test_smooth_transcription_uses_custom_prompts():
    """smooth_transcription mit custom_system/custom_user sendet diese ans Modell (Mock)."""
    from skill.text_smoothing import smooth_transcription
    sent = []
    class MockContent:
        def strip(self):
            return "ok"
    class Completions:
        def create(self, model=None, messages=None, temperature=None):
            sent.append(messages)
            msg = type("M", (), {"content": MockContent()})()
            choice = type("C", (), {"message": msg})()
            return type("R", (), {"choices": [choice]})()
    class Chat:
        completions = Completions()
    class MockClient:
        chat = Chat()
    smooth_transcription(MockClient(), "hi", "de", custom_system="MySystem", custom_user="MyUser")
    assert len(sent) == 1
    assert any(m.get("role") == "system" and m.get("content") == "MySystem" for m in sent[0])
    assert any(m.get("role") == "user" and "MyUser" in (m.get("content") or "") for m in sent[0])
    return True

def test_filter_hallucinations():
    """Halluzinationsfilter entfernt bekannte Phrasen."""
    if not HAS_SOUNDDEVICE:
        return "skip"
    from processing.transcription import _load_hallucinations, _filter_hallucinations
    path = os.path.join(APP_ROOT, "hallucination.json")
    assert os.path.isfile(path), "hallucination.json fehlt"
    hall = _load_hallucinations(path)
    assert isinstance(hall, dict)
    assert "de" in hall or "en" in hall
    # Text mit englischer Halluzination
    if "en" in hall and hall["en"]:
        pattern = hall["en"][0].strip()
        text_with = "Hello world. " + pattern + " More text."
        out = _filter_hallucinations(text_with, "en", hall)
        assert pattern not in out or out != text_with
    return True

def test_ui_design_labels():
    """Design-Check ohne GUI: Labels Sprache/Glaetten und Fensterbreite (ui/constants.py, ohne CTk)."""
    p = os.path.join(APP_ROOT, "ui", "constants.py")
    spec = importlib.util.spec_from_file_location("ui_constants", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.LABEL_SPRACHE == "Language", "Language label in UI"
    assert mod.LABEL_GLAETTEN == "Smooth", "Smooth label in UI"
    assert mod.WINDOW_WIDTH == 420, "Window width for layout"
    return True

def test_ui_import_and_create_no_display():
    """UI-Modul importierbar; create_status_window mit Dummy-Callbacks; Design-Check: Sprache + Glätten erkennbar."""
    if not HAS_CTK:
        return "skip"
    from ui import create_status_window
    refs = {}
    callbacks = {
        "start_stop_toggle": lambda: None,
        "start_recording": lambda: None,
        "stop_recording": lambda: None,
        "toggle_language": lambda: None,
        "toggle_keyboard": lambda: None,
        "quit_app": lambda: None,
        "toggle_minimal_mode": lambda: None,
        "toggle_info_compact": lambda: None,
        "toggle_transform_text": lambda: None,
        "open_api": lambda: None,
        "open_smoothing": lambda: None,
        "open_keys": lambda: None,
    }
    hotkeys = {"start_stop": "ctrl+y", "toggle_language": "alt+l", "toggle_keyboard": "alt+m", "quit": "alt+q"}
    initial = {"is_minimal_mode": True, "top_bar_compact": False, "transform_text_enabled": False, "current_language": "de"}
    win = create_status_window(callbacks, hotkeys, initial, refs)
    assert win is not None
    assert refs.get("window") is win
    assert refs.get("transform_text_var") is not None
    # Design: Sprache und Glätten im Interface (muss mit ui.constants uebereinstimmen)
    from ui.constants import LABEL_SPRACHE, LABEL_GLAETTEN
    lang_sw = refs.get("lang_switch")
    smooth_sw = refs.get("transform_switch")
    assert lang_sw is not None, "lang_switch in refs"
    assert smooth_sw is not None, "transform_switch in refs"
    assert (lang_sw.cget("text") or "").strip() == LABEL_SPRACHE
    assert (smooth_sw.cget("text") or "").strip() == LABEL_GLAETTEN
    win.destroy()
    return True

def run_all():
    cases = [
        ("config load_config", test_config_load),
        ("config settings load/save", test_settings_load_save),
        ("ui design labels (Sprache/Glätten)", test_ui_design_labels),
        ("processing get_available_microphones", test_get_available_microphones),
        ("processing audio_to_wav", test_audio_to_wav),
        ("processing record_audio (stop_event)", test_record_audio_stop_event),
        ("skill prompts de/en", test_prompts_de_en),
        ("skill smooth_transcription empty", test_smooth_transcription_empty),
        ("skill smooth_transcription custom prompts", test_smooth_transcription_uses_custom_prompts),
        ("transcription filter_hallucinations", test_filter_hallucinations),
        ("ui create_status_window", test_ui_import_and_create_no_display),
    ]
    failed = []
    skipped = 0
    for name, fn in cases:
        try:
            out = fn()
            if out == "skip":
                print("[SKIP]", name, "(Abhaengigkeit fehlt)")
                skipped += 1
            else:
                print("[OK]", name)
        except Exception as e:
            print("[FAIL]", name, "-", e)
            failed.append((name, e))
    if failed:
        print("\n", len(failed), "von", len(cases), "Tests fehlgeschlagen.", skipped, "uebersprungen.")
        sys.exit(1)
    print("\n", len(cases) - skipped, "Tests bestanden.", skipped, "uebersprungen (venv/uv fuer volle Suite).")
    return 0

if __name__ == "__main__":
    sys.exit(run_all())
