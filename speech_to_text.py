# =============================================================================
# SPEECH_TO_TEXT.PY – Einstiegspunkt der App
# =============================================================================
# Hier laeuft nur: Config laden, State halten, Callbacks definieren, Fenster
# erstellen, Tastatur-Polling und Mainloop. Keine Aufnahme-/Transkriptionslogik.
# UI lebt in ui/, Verarbeitung in processing/, Text-Glaettung in skill/text_smoothing/.
# =============================================================================

import os
import sys
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
    KEY_HOTKEY_START_STOP,
    DEFAULT_HOTKEY_START_STOP,
)
from processing import (
    record_audio,
    audio_to_wav,
    transcribe,
)
from skill.text_smoothing.prompts import get_prompts
from ui import (
    create_status_window,
    get_dialog_position_beside_parent,
    start_wave_animation,
    stop_wave_animation,
    start_reverse_animation,
    WINDOW_WIDTH,
    WINDOW_WIDTH_COMPACT,
    WINDOW_HEIGHT_COMPACT,
    WINDOW_HEIGHT_EXPANDED,
    SWITCH_SCALE,
    INFO_BTN_BG,
    INFO_BTN_BG_HOVER,
    INFO_BTN_TEXT_COLOR,
    LABEL_SPRACHE,
    LABEL_GLAETTEN,
)

# -----------------------------------------------------------------------------
# Konfiguration: config.json (Default) + settings.json (UI, ueberschreibt)
# Bei PyInstaller (frozen): App-Verzeichnis = Ordner der .exe (dort config/settings)
# -----------------------------------------------------------------------------
if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
config = load_config(APP_DIR)
settings = load_settings(APP_DIR)
api_key = (settings.get(KEY_API_KEY) or "").strip() or (config.get("api_key") or "").strip()
client = OpenAI(api_key=api_key or "dummy")

# Tastatur-Shortcuts: Keys wie sie von keyboard.is_pressed geprueft werden.
# start_stop aus settings.json, Rest fest.
HOTKEYS = {
    "start_stop": (settings.get(KEY_HOTKEY_START_STOP) or "").strip().lower().replace("strg", "ctrl") or DEFAULT_HOTKEY_START_STOP,
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
    "top_bar_compact": True,
    "stop_recording_event": threading.Event(),
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


def toggle_info_compact():
    """
    Togglet zwischen "Kompakt" (ultra-schmal, 1 Zeile, keine Labels) und "Ausgeklappt" (breit, 3 Zeilen).
    """
    win = refs.get("window")
    lang_switch = refs.get("lang_switch")
    lang_label = refs.get("lang_label")
    transform_switch = refs.get("transform_switch")
    sep = refs.get("sep")
    info_btn = refs.get("info_btn")
    button_frame = refs.get("button_frame")
    bottom_frame = refs.get("bottom_frame")
    content_frame = refs.get("content_frame")
    top_frame = refs.get("top_frame")
    
    if not all([win, lang_switch, lang_label, transform_switch, sep, info_btn, button_frame, bottom_frame]):
        return
        
    win.update_idletasks()
    wx, wy = win.winfo_x(), win.winfo_y()
    
    if state.get("top_bar_compact"):
        # Von Kompakt -> Ausgeklappt
        state["top_bar_compact"] = False
        _exp_w_lang = max(20, int(84 * SWITCH_SCALE))
        _exp_w_transform = max(20, int(76 * SWITCH_SCALE))
        lang_switch.configure(text=LABEL_SPRACHE, width=_exp_w_lang)
        transform_switch.configure(text=LABEL_GLAETTEN, width=_exp_w_transform)
        sep.grid(row=0, column=3, padx=8, pady=2)
        lang_label.grid(row=0, column=2, padx=4)
        info_btn.configure(fg_color=INFO_BTN_BG)
        anim_frame = refs.get("anim_frame")
        if anim_frame:
            anim_frame.grid_configure(padx=2)
        lang_switch.grid_configure(padx=(6, 4))
        transform_switch.grid_configure(padx=(4, 2))
        info_btn.grid_configure(padx=(2, 4))
        if content_frame:
            content_frame.pack_configure(padx=5, pady=5)
        if top_frame:
            top_frame.pack_configure(pady=2)
            
        button_frame.pack(pady=2, after=top_frame)
        bottom_frame.pack(pady=2, after=button_frame)
        
        win.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT_EXPANDED}+{wx}+{wy}")
    else:
        # Von Ausgeklappt -> Kompakt
        state["top_bar_compact"] = True
        _compact_sw = max(20, int(38 * SWITCH_SCALE))
        lang_switch.configure(text="", width=_compact_sw)
        transform_switch.configure(text="", width=_compact_sw)
        sep.grid_remove()
        lang_label.grid_remove()
        info_btn.configure(fg_color=INFO_BTN_BG)
        anim_frame = refs.get("anim_frame")
        if anim_frame:
            anim_frame.grid_configure(padx=(4, 0))
        lang_switch.grid_configure(padx=(0, 2))
        transform_switch.grid_configure(padx=(0, 6))
        info_btn.grid_configure(padx=(0, 4))
        if content_frame:
            content_frame.pack_configure(padx=0, pady=5)
        if top_frame:
            top_frame.pack_configure(pady=0)
            
        button_frame.pack_forget()
        bottom_frame.pack_forget()
        
        win.geometry(f"{WINDOW_WIDTH_COMPACT}x{WINDOW_HEIGHT_COMPACT}+{wx}+{wy}")
    win.update()


def toggle_transform_text():
    """Sync: Switch-Zustand (refs["transform_text_var"]) in state uebernehmen."""
    var = refs.get("transform_text_var")
    state["transform_text_enabled"] = var.get() if var else False


def open_api_dialog():
    """
    API-Dialog: API-Key anzeigen/eingeben/speichern, Modell fuer Smoother waehlen.
    Speichert in settings.json. Bei neuem Key wird state["client"] aktualisiert.
    """
    import customtkinter as ctk
    win = refs.get("window")
    if not win:
        return
        
    existing_dlg = refs.get("dlg_api")
    if existing_dlg and existing_dlg.winfo_exists():
        existing_dlg.destroy()
        refs["dlg_api"] = None
        return

    dlg = ctk.CTkToplevel(win)
    refs["dlg_api"] = dlg
    
    def on_close():
        refs["dlg_api"] = None
        dlg.destroy()
    dlg.protocol("WM_DELETE_WINDOW", on_close)

    dlg.title("API")
    dlg_w, dlg_h = 520, 280
    dlg.geometry(f"{dlg_w}x{dlg_h}")
    dlg.attributes("-topmost", True)
    dx, dy = get_dialog_position_beside_parent(win, dlg_w, dlg_h)
    dlg.geometry(f"{dlg_w}x{dlg_h}+{dx}+{dy}")

    px, py_section = 24, 16
    font_label = ("Arial", 12, "bold")
    font_body = ("Arial", 11)
    entry_w = 460

    # API Key
    ctk.CTkLabel(dlg, text="API Key (OpenAI):", font=font_label).pack(anchor="w", padx=px, pady=(py_section, 6))
    api_entry = ctk.CTkEntry(
        dlg, width=entry_w, height=36, font=font_body, show="*",
        placeholder_text="Leer = config.json oder bestehende Einstellungen"
    )
    api_entry.pack(padx=px, pady=(0, 6))
    api_entry.insert(0, load_settings(APP_DIR).get(KEY_API_KEY, ""))

    def toggle_show():
        if api_entry.cget("show") == "*":
            api_entry.configure(show="")
        else:
            api_entry.configure(show="*")
    ctk.CTkButton(dlg, text="Anzeigen", width=100, height=28, font=font_body, command=toggle_show).pack(anchor="w", padx=px, pady=(0, py_section))

    # Modell (Smoother / Chat-Completion)
    ctk.CTkLabel(dlg, text="Modell (Text-Glaettung):", font=font_label).pack(anchor="w", padx=px, pady=(0, 6))
    smoother_models = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]
    current_model = state.get("smoother_model", DEFAULT_SMOOTHER_MODEL)
    if current_model and current_model not in smoother_models:
        smoother_models = [current_model] + smoother_models
    model_var = ctk.StringVar(value=current_model)
    model_combo = ctk.CTkComboBox(dlg, values=smoother_models, variable=model_var, width=320, height=36, font=font_body)
    model_combo.pack(anchor="w", padx=px, pady=(0, py_section))

    def on_save():
        new_key = (api_entry.get() or "").strip()
        smoother_model = (model_var.get() or "").strip() or DEFAULT_SMOOTHER_MODEL
        data = load_settings(APP_DIR)
        data[KEY_API_KEY] = new_key
        data[KEY_SMOOTHER_MODEL] = smoother_model
        save_settings(APP_DIR, data)
        state["smoother_model"] = smoother_model
        state["client"] = OpenAI(api_key=new_key or (load_config(APP_DIR).get("api_key") or "").strip() or "dummy")
        refs["dlg_api"] = None
        dlg.destroy()

    ctk.CTkButton(
        dlg, text="Speichern", width=120, height=36, font=("Arial", 12, "bold"),
        command=on_save, fg_color="#1E88E5", hover_color="#1976D2"
    ).pack(pady=py_section)


def open_smoothing_dialog():
    """
    Smoothing-Dialog: Standard-Prompts aus Skill als Default, benutzerdefinierte Prompts
    bearbeiten, speichern, Default wieder laden (ueberschreibt aktuelle Eingabe mit Skill-Default).
    """
    import customtkinter as ctk
    win = refs.get("window")
    if not win:
        return
        
    existing_dlg = refs.get("dlg_smoothing")
    if existing_dlg and existing_dlg.winfo_exists():
        existing_dlg.destroy()
        refs["dlg_smoothing"] = None
        return

    dlg = ctk.CTkToplevel(win)
    refs["dlg_smoothing"] = dlg
    
    def on_close():
        refs["dlg_smoothing"] = None
        dlg.destroy()
    dlg.protocol("WM_DELETE_WINDOW", on_close)

    dlg.title("Smoothing")
    dlg_w, dlg_h = 620, 640
    dlg.geometry(f"{dlg_w}x{dlg_h}")
    dlg.attributes("-topmost", True)
    dx, dy = get_dialog_position_beside_parent(win, dlg_w, dlg_h)
    dlg.geometry(f"{dlg_w}x{dlg_h}+{dx}+{dy}")

    scroll = ctk.CTkScrollableFrame(dlg, width=dlg_w - 20, height=dlg_h - 100, fg_color="transparent")
    scroll.pack(fill="both", expand=True, padx=(10, 0), pady=(10, 10))

    px, py_section = 24, 14
    font_section = ("Arial", 14, "bold")
    font_label = ("Arial", 12, "bold")
    font_body = ("Arial", 11)
    textbox_w = 560

    ctk.CTkLabel(
        scroll, text="Text-Glaettung: Prompts fuer Korrektur nach Spracherkennung (wenn 'Glaetten' aktiv).",
        font=("Arial", 10), text_color="#AAAAAA"
    ).pack(anchor="w", padx=px, pady=(0, 8))

    use_custom_var = ctk.BooleanVar(value=state.get("use_custom_smoother", False))
    ctk.CTkCheckBox(
        scroll, text="Benutzerdefinierte Prompts verwenden (sonst Standard DE/EN)", variable=use_custom_var,
        font=font_body, height=28, checkbox_width=22, checkbox_height=22
    ).pack(anchor="w", padx=px, pady=(0, py_section))

    ctk.CTkLabel(scroll, text="System-Prompt (Rolle):", font=font_label).pack(anchor="w", padx=px, pady=(4, 4))
    sys_text = ctk.CTkTextbox(scroll, width=textbox_w, height=76, font=font_body)
    sys_text.pack(padx=px, pady=(0, 8))
    sys_text.insert("1.0", state.get("custom_smoother_system", ""))
    ctk.CTkLabel(scroll, text="User-Prompt (Anweisung + Platzhalter fuer Originaltext):", font=font_body).pack(anchor="w", padx=px, pady=(4, 4))
    user_text = ctk.CTkTextbox(scroll, width=textbox_w, height=100, font=font_body)
    user_text.pack(padx=px, pady=(0, 12))

    # Buttons: Default laden (aus Skill), Speichern
    btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
    btn_frame.pack(anchor="w", padx=px, pady=(0, 8))

    def load_default():
        prompts_de = get_prompts("de")
        sys_text.delete("1.0", "end")
        user_text.delete("1.0", "end")
        sys_text.insert("1.0", prompts_de.get("system", ""))
        user_text.insert("1.0", prompts_de.get("user", ""))

    ctk.CTkButton(
        btn_frame, text="Default laden", width=120, height=32, font=font_body,
        command=load_default, fg_color="#555555", hover_color="#666666"
    ).pack(side="left", padx=(0, 8))
    ctk.CTkButton(
        btn_frame, text="Speichern", width=120, height=32, font=("Arial", 12, "bold"),
        command=lambda: _smoothing_save(dlg, use_custom_var, sys_text, user_text),
        fg_color="#1E88E5", hover_color="#1976D2"
    ).pack(side="left")

    def _smoothing_save(dialog, use_custom_var, sys_textbox, user_textbox):
        use_custom = use_custom_var.get()
        custom_sys = (sys_textbox.get("1.0", "end") or "").strip()
        custom_usr = (user_textbox.get("1.0", "end") or "").strip()
        data = load_settings(APP_DIR)
        data[KEY_USE_CUSTOM_SMOOTHER] = use_custom
        data[KEY_CUSTOM_SMOOTHER_SYSTEM] = custom_sys
        data[KEY_CUSTOM_SMOOTHER_USER] = custom_usr
        save_settings(APP_DIR, data)
        state["use_custom_smoother"] = use_custom
        state["custom_smoother_system"] = custom_sys
        state["custom_smoother_user"] = custom_usr
        refs["dlg_smoothing"] = None
        dialog.destroy()


def _tk_bind_key(key_str):
    """Hotkey-String fuer Tk: 'ctrl+y' -> 'Control-y', 'alt+l' -> 'Alt-l'."""
    s = (key_str or "").strip().lower()
    s = s.replace("ctrl", "Control").replace("alt", "Alt").replace("+", "-")
    return s


def open_keys_dialog():
    """
    Dialog: Start/Stop-Kombination aendern (Default ctrl+y). Speichert in settings.json,
    aktualisiert HOTKEYS und Tk-Binding sofort.
    """
    import customtkinter as ctk
    win = refs.get("window")
    if not win:
        return
        
    existing_dlg = refs.get("dlg_keys")
    if existing_dlg and existing_dlg.winfo_exists():
        existing_dlg.destroy()
        refs["dlg_keys"] = None
        return

    dlg = ctk.CTkToplevel(win)
    refs["dlg_keys"] = dlg
    
    def on_close():
        refs["dlg_keys"] = None
        dlg.destroy()
    dlg.protocol("WM_DELETE_WINDOW", on_close)

    dlg.title("Keyboard")
    dlg_w, dlg_h = 420, 200
    dlg.geometry(f"{dlg_w}x{dlg_h}")
    dlg.attributes("-topmost", True)
    dx, dy = get_dialog_position_beside_parent(win, dlg_w, dlg_h)
    dlg.geometry(f"{dlg_w}x{dlg_h}+{dx}+{dy}")

    px, py_section = 24, 14
    font_label = ("Arial", 12, "bold")
    font_body = ("Arial", 11)
    entry_w = 280

    ctk.CTkLabel(dlg, text="Start/Stop (z.B. ctrl+y, ctrl+shift+y):", font=font_label).pack(anchor="w", padx=px, pady=(py_section, 6))
    key_entry = ctk.CTkEntry(dlg, width=entry_w, height=36, font=font_body)
    key_entry.pack(padx=px, pady=(0, 8))
    key_entry.insert(0, HOTKEYS["start_stop"])

    btn_frame = ctk.CTkFrame(dlg, fg_color="transparent")
    btn_frame.pack(anchor="w", padx=px, pady=(0, 8))

    def load_default():
        key_entry.delete(0, "end")
        key_entry.insert(0, DEFAULT_HOTKEY_START_STOP)

    def on_save():
        new_val = (key_entry.get() or "").strip().lower().replace("strg", "ctrl") or DEFAULT_HOTKEY_START_STOP
        data = load_settings(APP_DIR)
        data[KEY_HOTKEY_START_STOP] = new_val
        save_settings(APP_DIR, data)
        HOTKEYS["start_stop"] = new_val
        # Tk-Binding aktualisieren: altes unbinden, neues binden
        old_tk = refs.get("hotkey_start_stop_tk")
        if old_tk:
            try:
                win.unbind(f"<{old_tk}>")
            except Exception:
                pass
        new_tk = _tk_bind_key(new_val)
        win.bind(f"<{new_tk}>", lambda e: start_stop_toggle())
        refs["hotkey_start_stop_tk"] = new_tk
        refs["dlg_keys"] = None
        dlg.destroy()

    ctk.CTkButton(btn_frame, text="Default", width=90, height=32, font=font_body, command=load_default, fg_color="#555555", hover_color="#666666").pack(side="left", padx=(0, 8))
    ctk.CTkButton(btn_frame, text="Speichern", width=100, height=32, font=("Arial", 12, "bold"), command=on_save, fg_color="#1E88E5", hover_color="#1976D2").pack(side="left")
    dlg.focus_force()


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
    initial_state = {
        "top_bar_compact": state["top_bar_compact"],
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
        "toggle_info_compact": toggle_info_compact,
        "toggle_transform_text": toggle_transform_text,
        "open_api": open_api_dialog,
        "open_smoothing": open_smoothing_dialog,
        "open_keys": open_keys_dialog,
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
