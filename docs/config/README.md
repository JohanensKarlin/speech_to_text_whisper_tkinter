# config/ – Konfiguration

Damit du schnell weisst: Wo die Config herkommt, wo Benutzereinstellungen liegen, und wo du erweitern musst.

---

## Zweck

- **config.json** (Default): `load_config(config_dir)` laedt sie; wenn die Datei fehlt, leeres Dict. Enthaelt z. B. `api_key`.
- **settings.json** (UI-Einstellungen): Wird ueber den Einstellungen-Dialog gespeichert. Enthaelt: `api_key`, `use_custom_smoother`, `custom_smoother_system`, `custom_smoother_user`, `smoother_model` (Chat-Modell fuer Text-Glaettung, Default gpt-4o-mini).
- **Prioritaet:** API-Key = settings["api_key"] oder config["api_key"]. Custom-Smoother-Felder kommen aus settings.

---

## Schnittstelle

- **load_config(config_dir=None)**  
  - `config_dir`: Verzeichnis, in dem `config.json` liegt. Wenn `None`, wird das Parent-Verzeichnis von `config/` genommen (also Projektroot).  
  - Return: Dict, mindestens Key `"api_key"`. Weitere Keys sind moeglich und werden nicht abgefragt.

---

## Wo du ansetzt

- **Neue Einstellungen (z. B. Modell, Hotkeys):** In `config.json` neue Keys anlegen, in `load_config` nichts aendern noetig. In `speech_to_text.py` (oder wo die Config genutzt wird) die neuen Keys aus `config` lesen.
- **Anderes Format (z. B. Umgebungsvariablen):** In `config/load.py` die Logik anpassen und weiterhin ein Dict zurueckgeben, das mindestens `api_key` enthaelt.
- **Config-Pfad aendern:** `load_config` so aufrufen, dass das richtige Verzeichnis uebergeben wird; Standard ist Projektroot.

---

## Dateien

- `config/load.py` – `load_config` (config.json, bei Fehlen leeres Dict).
- `config/settings.py` – `load_settings`, `save_settings` (settings.json); Keys: api_key, use_custom_smoother, custom_smoother_system, custom_smoother_user, smoother_model.
- Im Projektroot: `config.json` (Default), `settings.json` (ueber Einstellungen-Dialog; beide in .gitignore).

API-Key: zuerst aus settings.json, sonst aus config.json. Custom-Smoother nur aus settings.
