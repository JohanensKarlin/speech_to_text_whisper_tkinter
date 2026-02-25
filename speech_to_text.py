# =============================================================================
# SPEECH_TO_TEXT.PY – Einstiegspunkt der App
# =============================================================================
# Hier laeuft nur: Config laden, State halten, Callbacks definieren, Fenster
# erstellen, Tastatur-Polling und Mainloop. Keine Aufnahme-/Transkriptionslogik.
# UI lebt in ui/, Verarbeitung in processing/, Text-Glaettung in skill/text_smoothing/.
# =============================================================================

import os
import threading
import time

import keyboard
import pyautogui
import pyperclip
from openai import OpenAI

from config import (
    load_config,
    load_settings,
    save_settings,
    KEY_API_KEY,
    KEY_USE_CUSTOM_SMOOTHER,
    KEY_CUSTOM_SMOOTHER_SYSTEM,
    KEY_CUSTOM_SMOOTHER_USER,
    KEY_SMOOTHER_MODEL,
    DEFAULT_SMOOTHER_MODEL,
)
from processing import (
    get_available_microphones,
    record_audio,
    audio_to_wav,
    transcribe,
)
from skill.text_smoothing.prompts import get_prompts
from ui import (
    create_status_window,
    start_wave_animation,
    stop_wave_animation,
    start_reverse_animation,
    WINDOW_WIDTH,
)

# -----------------------------------------------------------------------------
# Konfiguration: config.json (Default) + settings.json (UI, ueberschreibt)
# -----------------------------------------------------------------------------
APP_DIR = os.path.dirname(os.path.abspath(__file__))
config = load_config(APP_DIR)
settings = load_settings(APP_DIR)
api_key = (settings.get(KEY_API_KEY) or "").strip() or (config.get("api_key") or "").strip()
client = OpenAI(api_key=api_key or "dummy")

# Tastatur-Shortcuts: Keys wie sie von keyboard.is_pressed geprueft werden
HOTKEYS = {
    "start_stop": "ctrl+y",
    "toggle_language": "alt+l",
    "toggle_keyboard": "alt+m",
    "quit": "alt+q",
}

# -----------------------------------------------------------------------------
# State – zentrale Daten, die von Callbacks und process_recording gelesen werden
# -----------------------------------------------------------------------------
state = {
    "is_recording": False,
    "current_language": "de",
    "transform_text_enabled": False,
    "selected_mic_index": 0,
    "keyboard_enabled": True,
    "is_minimal_mode": True,
    "stop_recording_event": threading.Event(),
    "available_mics": [],
    "client": client,  # OpenAI-Client; wird bei Settings-Speichern (neuer API-Key) ersetzt
    "use_custom_smoother": settings.get(KEY_USE_CUSTOM_SMOOTHER, False),
    "custom_smoother_system": settings.get(KEY_CUSTOM_SMOOTHER_SYSTEM, ""),
    "custom_smoother_user": settings.get(KEY_CUSTOM_SMOOTHER_USER, ""),
    "smoother_model": settings.get(KEY_SMOOTHER_MODEL, DEFAULT_SMOOTHER_MODEL),
}
# refs wird von create_status_window() befuellt: window, lang_label, transform_text_var,
# button_frame, bottom_frame, etc. Callbacks nutzen refs um UI-Elemente zu aktualisieren.
refs = {}


def _paste_text(text):
    """Text in Zwischenablage und per Strg+V einfügen (aktivem Fenster)."""
    if text:
        pyperclip.copy(text)
        pyautogui.hotkey("ctrl", "v")


# -----------------------------------------------------------------------------
# Aufnahme-Pipeline (läuft im Hintergrund-Thread)
# -----------------------------------------------------------------------------
def process_recording():
    """
    Vollständiger Ablauf: Animation starten -> Aufnahme bis stop_event ->
    WAV bauen -> transcribe() (Whisper + Halluzinationsfilter + optional Glaettung) ->
    Ergebnis einfügen. Animation start/stop wird hier gesteuert, Logik in ui.animation.
    """
    state["is_recording"] = True
    state["stop_recording_event"].clear()
    start_wave_animation()
    try:
        audio_data = record_audio(
            state["selected_mic_index"],
            state["stop_recording_event"],
        )
        stop_wave_animation()
        if audio_data.size == 0:
            print("Keine Audiodaten aufgenommen.")
            return
        start_reverse_animation()
        wav_file = audio_to_wav(audio_data)
        hallucination_path = os.path.join(APP_DIR, "hallucination.json")
        transform_var = refs.get("transform_text_var")
        transform_enabled = transform_var.get() if transform_var else False
        use_custom = state.get("use_custom_smoother") and state.get("custom_smoother_system") and state.get("custom_smoother_user")
        custom_sys = state.get("custom_smoother_system") if use_custom else None
        custom_usr = state.get("custom_smoother_user") if use_custom else None
        text = transcribe(
            state["client"],
            wav_file,
            language=state["current_language"],
            hallucination_path=hallucination_path,
            transform_enabled=transform_enabled,
            custom_smoother_system=custom_sys,
            custom_smoother_user=custom_usr,
            smoother_model=state.get("smoother_model") or DEFAULT_SMOOTHER_MODEL,
        )
        stop_wave_animation()
        if text:
            _paste_text(text)
            print(f"Transkription abgeschlossen: {text}")
        else:
            print("Transkription ergab keinen Text.")
    except Exception as e:
        print(f"Fehler: {e}")
        stop_wave_animation()
    finally:
        state["is_recording"] = False


def start_recording():
    """Startet process_recording in einem Daemon-Thread, nur wenn nicht schon am Aufnehmen."""
    if not state["is_recording"]:
        threading.Thread(target=process_recording, daemon=True).start()


def stop_recording():
    """Setzt stop_event; record_audio() in processing bricht dann die Schleife ab."""
    state["stop_recording_event"].set()


def start_stop_toggle():
    """Eine Taste (Strg+Y): je nach is_recording entweder Start oder Stop. Debounce 0.3s."""
    if state["is_recording"]:
        stop_recording()
    else:
        start_recording()
    time.sleep(0.3)


# -----------------------------------------------------------------------------
# Callbacks fuer UI (Fenster ruft diese bei Klick/Shortcut auf)
# -----------------------------------------------------------------------------
def toggle_language():
    """Wechselt current_language de <-> en und aktualisiert Label + Switch in refs."""
    lang_label = refs.get("lang_label")
    lang_switch_var = refs.get("lang_switch_var")
    if state["current_language"] == "de":
        state["current_language"] = "en"
        label_text = "EN"
    else:
        state["current_language"] = "de"
        label_text = "DE"
    if lang_label:
        lang_label.configure(text=label_text)
    if lang_switch_var:
        lang_switch_var.set(label_text)


def toggle_keyboard():
    """Schaltet Tastatur-Shortcuts an/aus und aktualisiert Button-Text und Farbe."""
    state["keyboard_enabled"] = not state["keyboard_enabled"]
    kb_btn = refs.get("keyboard_button")
    if kb_btn:
        if state["keyboard_enabled"]:
            kb_btn.configure(text="Keyboard: On", fg_color="#1E88E5")
        else:
            kb_btn.configure(text="Keyboard: Off", fg_color="#666666")


def quit_app():
    """Fenster schliessen; poll() erkennt winfo_exists() False und beendet die Schleife."""
    win = refs.get("window")
    if win:
        win.destroy()


def toggle_minimal_mode():
    """Fenster zwischen Minimal (nur Leiste) und Normal (mit Start/Stop/Mic/Tastatur/Beenden) umschalten."""
    win = refs.get("window")
    button_frame = refs.get("button_frame")
    bottom_frame = refs.get("bottom_frame")
    content_frame = refs.get("content_frame")
    top_frame = refs.get("top_frame")
    if not all([win, button_frame, bottom_frame, content_frame, top_frame]):
        return
    w = WINDOW_WIDTH
    if state["is_minimal_mode"]:
        button_frame.pack(pady=2, after=top_frame)
        bottom_frame.pack(pady=2, after=button_frame)
        state["is_minimal_mode"] = False
        win.update_idletasks()
        win.geometry(f"{w}x120")
    else:
        button_frame.pack_forget()
        bottom_frame.pack_forget()
        state["is_minimal_mode"] = True
        win.update_idletasks()
        win.geometry(f"{w}x40")
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    h = 120 if not state["is_minimal_mode"] else 40
    win.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")
    win.update()


def select_microphone():
    """Oeffnet Modal-Dialog mit Radiobuttons; gewaehltes Geraet in state["selected_mic_index"]."""
    import customtkinter as ctk
    win = refs.get("window")
    if not state["available_mics"]:
        state["available_mics"] = get_available_microphones()
    mic_win = ctk.CTkToplevel(win)
    mic_win.title("Select microphone")
    mic_win.geometry("300x250")
    mic_win.attributes("-topmost", True)
    sw = mic_win.winfo_screenwidth()
    sh = mic_win.winfo_screenheight()
    mic_win.geometry(f"300x250+{(sw - 300) // 2}+{(sh - 250) // 2}")
    ctk.CTkLabel(mic_win, text="Available microphones:", font=("Arial", 14, "bold")).pack(pady=(15, 5))
    list_frame = ctk.CTkFrame(mic_win, fg_color="transparent")
    list_frame.pack(fill="both", expand=True, padx=10, pady=5)
    scroll = ctk.CTkScrollableFrame(list_frame, width=280, height=150)
    scroll.pack(fill="both", expand=True)
    selected_var = ctk.IntVar(value=state["selected_mic_index"])
    for mic in state["available_mics"]:
        ctk.CTkRadioButton(
            scroll, text=mic["name"], value=mic["index"],
            variable=selected_var, font=("Arial", 12),
        ).pack(anchor="w", pady=2, padx=5)

    def on_ok():
        state["selected_mic_index"] = selected_var.get()
        mic_win.destroy()

    ctk.CTkButton(
        mic_win, text="OK", command=on_ok,
        width=100, height=30, corner_radius=10,
        fg_color="#1E88E5", hover_color="#1976D2",
    ).pack(pady=15)


def toggle_transform_text():
    """Sync: Switch-Zustand (refs["transform_text_var"]) in state uebernehmen."""
    var = refs.get("transform_text_var")
    state["transform_text_enabled"] = var.get() if var else False


def open_settings():
    """Opens settings dialog: API key, text smoothing (system/user prompts). Saves to settings.json."""
    import customtkinter as ctk
    win = refs.get("window")
    if not win:
        return
    dlg = ctk.CTkToplevel(win)
    dlg.title("Settings")
    dlg_w, dlg_h = 620, 760
    dlg.geometry(f"{dlg_w}x{dlg_h}")
    dlg.attributes("-topmost", True)
    sw = dlg.winfo_screenwidth()
    sh = dlg.winfo_screenheight()
    dlg.geometry(f"{dlg_w}x{dlg_h}+{(sw - dlg_w) // 2}+{(sh - dlg_h) // 2}")

    # Scrollbares Frame: Inhalt scrollbar, Scrollleiste rechts
    scroll = ctk.CTkScrollableFrame(dlg, width=dlg_w - 20, height=dlg_h - 80, fg_color="transparent")
    scroll.pack(fill="both", expand=True, padx=(10, 0), pady=(10, 10))

    px, py_section = 24, 20
    font_section = ("Arial", 14, "bold")
    font_label = ("Arial", 12, "bold")
    font_body = ("Arial", 11)
    font_small = ("Arial", 11)
    entry_w = 560
    textbox_w = 560

    # API Key
    ctk.CTkLabel(scroll, text="API Key (OpenAI):", font=font_label).pack(anchor="w", padx=px, pady=(py_section, 6))
    api_entry = ctk.CTkEntry(
        scroll, width=entry_w, height=36, font=font_body, show="*",
        placeholder_text="Leave empty = use config.json or existing settings"
    )
    api_entry.pack(padx=px, pady=(0, 8))
    api_entry.insert(0, load_settings(APP_DIR).get(KEY_API_KEY, ""))
    def toggle_show():
        if api_entry.cget("show") == "*":
            api_entry.configure(show="")
        else:
            api_entry.configure(show="*")
    ctk.CTkButton(scroll, text="Show", width=100, height=32, font=font_body, command=toggle_show).pack(anchor="w", padx=px, pady=(0, py_section))

    # Text smoothing (used when "Smooth" is enabled in the main window)
    ctk.CTkLabel(scroll, text="Text smoothing (Smoother):", font=font_section).pack(anchor="w", padx=px, pady=(0, 4))
    ctk.CTkLabel(
        scroll, text="Used when you turn on 'Smooth' in the main bar. Prompts below define how transcription text is corrected.",
        font=("Arial", 10), text_color="#AAAAAA"
    ).pack(anchor="w", padx=px, pady=(0, 6))
    ctk.CTkLabel(scroll, text="Model (Chat-Completion):", font=font_body).pack(anchor="w", padx=px, pady=(4, 4))
    smoother_models = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]
    current_model = state.get("smoother_model", DEFAULT_SMOOTHER_MODEL)
    if current_model and current_model not in smoother_models:
        smoother_models = [current_model] + smoother_models
    model_var = ctk.StringVar(value=current_model)
    model_combo = ctk.CTkComboBox(scroll, values=smoother_models, variable=model_var, width=320, height=36, font=font_body)
    model_combo.pack(anchor="w", padx=px, pady=(0, 10))
    use_custom_var = ctk.BooleanVar(value=state.get("use_custom_smoother", False))
    ctk.CTkCheckBox(
        scroll, text="Use custom prompts (otherwise default DE/EN)", variable=use_custom_var,
        font=font_body, height=28, checkbox_width=22, checkbox_height=22
    ).pack(anchor="w", padx=px, pady=(4, py_section))

    # Default prompts (read-only)
    def_prompts_de = get_prompts("de")
    ctk.CTkLabel(scroll, text="Default prompts (when not using custom):", font=font_label).pack(anchor="w", padx=px, pady=(0, 6))
    ctk.CTkLabel(scroll, text="DE System:", font=font_small).pack(anchor="w", padx=px, pady=(4, 2))
    default_sys_de = ctk.CTkTextbox(scroll, width=textbox_w, height=56, font=font_small, fg_color="#2b2b2b")
    default_sys_de.pack(padx=px, pady=(0, 6))
    default_sys_de.insert("1.0", def_prompts_de.get("system", ""))
    default_sys_de.configure(state="disabled")
    ctk.CTkLabel(scroll, text="DE User:", font=font_small).pack(anchor="w", padx=px, pady=(4, 2))
    default_usr_de = ctk.CTkTextbox(scroll, width=textbox_w, height=88, font=font_small, fg_color="#2b2b2b")
    default_usr_de.pack(padx=px, pady=(0, py_section))
    default_usr_de.insert("1.0", def_prompts_de.get("user", ""))
    default_usr_de.configure(state="disabled")

    # Custom prompts (override defaults)
    ctk.CTkLabel(scroll, text="Custom prompts (override default):", font=font_label).pack(anchor="w", padx=px, pady=(0, 6))
    ctk.CTkLabel(scroll, text="System prompt (role):", font=font_body).pack(anchor="w", padx=px, pady=(4, 4))
    sys_text = ctk.CTkTextbox(scroll, width=textbox_w, height=76, font=font_body)
    sys_text.pack(padx=px, pady=(0, 8))
    sys_text.insert("1.0", state.get("custom_smoother_system", ""))
    ctk.CTkLabel(scroll, text="User prompt (instruction + placeholder for original text):", font=font_body).pack(anchor="w", padx=px, pady=(4, 4))
    user_text = ctk.CTkTextbox(scroll, width=textbox_w, height=100, font=font_body)
    user_text.pack(padx=px, pady=(0, 8))
    user_text.insert("1.0", state.get("custom_smoother_user", ""))

    def on_save():
        new_key = (api_entry.get() or "").strip()
        use_custom = use_custom_var.get()
        custom_sys = (sys_text.get("1.0", "end") or "").strip()
        custom_usr = (user_text.get("1.0", "end") or "").strip()
        smoother_model = (model_var.get() or "").strip() or DEFAULT_SMOOTHER_MODEL
        data = {
            KEY_API_KEY: new_key,
            KEY_USE_CUSTOM_SMOOTHER: use_custom,
            KEY_CUSTOM_SMOOTHER_SYSTEM: custom_sys,
            KEY_CUSTOM_SMOOTHER_USER: custom_usr,
            KEY_SMOOTHER_MODEL: smoother_model,
        }
        save_settings(APP_DIR, data)
        state["use_custom_smoother"] = use_custom
        state["custom_smoother_system"] = custom_sys
        state["custom_smoother_user"] = custom_usr
        state["smoother_model"] = smoother_model
        effective_key = new_key or (load_config(APP_DIR).get("api_key") or "").strip()
        state["client"] = OpenAI(api_key=effective_key or "dummy")
        dlg.destroy()

    ctk.CTkLabel(scroll, text="Saves API key and all settings above.", font=("Arial", 10), text_color="#AAAAAA").pack(pady=(4, 0))
    ctk.CTkButton(
        scroll, text="Save", width=140, height=40, font=("Arial", 12, "bold"),
        command=on_save, fg_color="#1E88E5", hover_color="#1976D2"
    ).pack(pady=py_section)


# -----------------------------------------------------------------------------
# Tastatur-Polling (alle 100 ms); nur wenn keyboard_enabled und Fenster lebt
# -----------------------------------------------------------------------------
def check_keyboard_input():
    """
    Prueft HOTKEYS; bei Treffer passenden Callback ausfuehren.
    Return True = weiter pollen, False = Fenster beenden (quit), dann poll() ruft w.quit() auf.
    """
    if not state["keyboard_enabled"]:
        return True
    win = refs.get("window")
    try:
        if not win or not win.winfo_exists():
            return False
    except Exception:
        return False
    if keyboard.is_pressed(HOTKEYS["start_stop"]):
        start_stop_toggle()
        return True
    if keyboard.is_pressed(HOTKEYS["toggle_language"]):
        toggle_language()
        time.sleep(0.3)
        return True
    if keyboard.is_pressed(HOTKEYS["toggle_keyboard"]):
        toggle_keyboard()
        time.sleep(0.3)
        return True
    if keyboard.is_pressed(HOTKEYS["quit"]):
        quit_app()
        return False
    return True


def main():
    """
    Mikrofone laden, Callbacks + initial_state bauen, Fenster erstellen (refs wird befuellt),
    dann poll()-Schleife starten und mainloop. Nach quit_app() erkennt poll() tote Fenster und beendet.
    """
    state["available_mics"] = get_available_microphones()
    initial_state = {
        "is_minimal_mode": state["is_minimal_mode"],
        "transform_text_enabled": state["transform_text_enabled"],
        "current_language": state["current_language"],
    }
    callbacks = {
        "start_stop_toggle": start_stop_toggle,
        "start_recording": start_recording,
        "stop_recording": stop_recording,
        "toggle_language": toggle_language,
        "toggle_keyboard": toggle_keyboard,
        "quit_app": quit_app,
        "toggle_minimal_mode": toggle_minimal_mode,
        "select_microphone": select_microphone,
        "toggle_transform_text": toggle_transform_text,
        "open_settings": open_settings,
    }
    create_status_window(callbacks, HOTKEYS, initial_state, refs)
    print("Ctrl+Y Start/Stop, Alt+Q Quit.")

    def poll():
        try:
            w = refs.get("window")
            if not w or not w.winfo_exists():
                return
        except Exception:
            return
        if check_keyboard_input():
            try:
                w.after(100, poll)
            except Exception:
                pass
        else:
            try:
                w.quit()
            except Exception:
                pass

    poll()
    refs["window"].mainloop()


if __name__ == "__main__":
    main()
