# =============================================================================
# CONFIG/SETTINGS.PY – Benutzereinstellungen (API-Key, Custom Text-Glaettung)
# =============================================================================
# settings.json im App-Root: Ueberschreibt/ergaenzt config.json. Ermoeglicht
# Konfiguration ohne Script-Aenderung (API-Key, eigene Prompts fuer Smoother).
# =============================================================================

import json
import os

SETTINGS_FILENAME = "settings.json"

# Keys in settings.json
KEY_API_KEY = "api_key"
KEY_USE_CUSTOM_SMOOTHER = "use_custom_smoother"
KEY_CUSTOM_SMOOTHER_SYSTEM = "custom_smoother_system"
KEY_CUSTOM_SMOOTHER_USER = "custom_smoother_user"
KEY_SMOOTHER_MODEL = "smoother_model"
KEY_HOTKEY_START_STOP = "hotkey_start_stop"
KEY_PROVIDER = "provider"
KEY_AZURE_ENDPOINT_URL = "azure_endpoint_url"
KEY_AZURE_API_KEY = "azure_api_key"
KEY_TRANSCRIBE_MODEL = "transcribe_model"

DEFAULT_SMOOTHER_MODEL = "gpt-4o-mini"
DEFAULT_HOTKEY_START_STOP = "ctrl+y"
DEFAULT_PROVIDER = "openai"
DEFAULT_TRANSCRIBE_MODEL = "gpt-4o-mini-transcribe"


def _path(app_dir):
    return os.path.join(app_dir, SETTINGS_FILENAME)


def load_settings(app_dir):
    """
    Laedt settings.json. Return: Dict mit api_key, use_custom_smoother,
    custom_smoother_system, custom_smoother_user. Leeres Dict wenn Datei fehlt.
    """
    p = _path(app_dir)
    if not os.path.isfile(p):
        return {}
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {}
    return {
        KEY_API_KEY: data.get(KEY_API_KEY, ""),
        KEY_USE_CUSTOM_SMOOTHER: bool(data.get(KEY_USE_CUSTOM_SMOOTHER, False)),
        KEY_CUSTOM_SMOOTHER_SYSTEM: (data.get(KEY_CUSTOM_SMOOTHER_SYSTEM) or "").strip(),
        KEY_CUSTOM_SMOOTHER_USER: (data.get(KEY_CUSTOM_SMOOTHER_USER) or "").strip(),
        KEY_SMOOTHER_MODEL: (data.get(KEY_SMOOTHER_MODEL) or "").strip() or DEFAULT_SMOOTHER_MODEL,
        KEY_HOTKEY_START_STOP: (data.get(KEY_HOTKEY_START_STOP) or "").strip().lower().replace("strg", "ctrl") or DEFAULT_HOTKEY_START_STOP,
        KEY_PROVIDER: (data.get(KEY_PROVIDER) or DEFAULT_PROVIDER).strip().lower(),
        KEY_AZURE_ENDPOINT_URL: (data.get(KEY_AZURE_ENDPOINT_URL) or "").strip(),
        KEY_AZURE_API_KEY: (data.get(KEY_AZURE_API_KEY) or "").strip(),
        KEY_TRANSCRIBE_MODEL: (data.get(KEY_TRANSCRIBE_MODEL) or "").strip() or DEFAULT_TRANSCRIBE_MODEL,
    }


def save_settings(app_dir, data):
    """
    Speichert data in settings.json. data: Dict mit KEY_* Keys (api_key, ...).
    """
    p = _path(app_dir)
    out = {
        KEY_API_KEY: (data.get(KEY_API_KEY) or ""),
        KEY_USE_CUSTOM_SMOOTHER: bool(data.get(KEY_USE_CUSTOM_SMOOTHER, False)),
        KEY_CUSTOM_SMOOTHER_SYSTEM: (data.get(KEY_CUSTOM_SMOOTHER_SYSTEM) or ""),
        KEY_CUSTOM_SMOOTHER_USER: (data.get(KEY_CUSTOM_SMOOTHER_USER) or ""),
        KEY_SMOOTHER_MODEL: (data.get(KEY_SMOOTHER_MODEL) or "").strip() or DEFAULT_SMOOTHER_MODEL,
        KEY_HOTKEY_START_STOP: (data.get(KEY_HOTKEY_START_STOP) or "").strip().lower().replace("strg", "ctrl") or DEFAULT_HOTKEY_START_STOP,
        KEY_PROVIDER: (data.get(KEY_PROVIDER) or DEFAULT_PROVIDER).strip().lower(),
        KEY_AZURE_ENDPOINT_URL: (data.get(KEY_AZURE_ENDPOINT_URL) or "").strip(),
        KEY_AZURE_API_KEY: (data.get(KEY_AZURE_API_KEY) or "").strip(),
        KEY_TRANSCRIBE_MODEL: (data.get(KEY_TRANSCRIBE_MODEL) or "").strip() or DEFAULT_TRANSCRIBE_MODEL,
    }
    with open(p, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
