# =============================================================================
# CONFIG/LOAD.PY – Konfiguration aus config.json
# =============================================================================
# Einzige Abhaengigkeit: Pfad zum App-Root. Erwartet config.json mit z.B. api_key.
# Erweiterbar um weitere Keys (Hotkeys, Modellnamen, etc.).
# =============================================================================

import json
import os


def load_config(config_dir=None):
    """
    Laedt config.json aus dem angegebenen Verzeichnis (App-Root).
    config_dir: Verzeichnis, in dem config.json liegt. Wenn None: Parent von config/.
    Returns: Dict (z.B. {"api_key": "..."}). Leeres Dict wenn Datei fehlt (dann nur Settings).
    """
    if config_dir is None:
        config_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(config_dir, "config.json")
    if not os.path.isfile(config_path):
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)
