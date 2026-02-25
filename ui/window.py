# =============================================================================
# UI/WINDOW.PY – Schwebendes Statusfenster (nur Aufbau, keine Logik)
# =============================================================================
# Erstellt CTk-Fenster, Frames, Buttons, Switches, Animation-Canvas. Alle Aktionen
# ueber callbacks (von speech_to_text.py). refs wird mit window, lang_label,
# transform_text_var, button_frame, etc. befuellt, damit Callbacks die UI updaten.
# =============================================================================

import customtkinter as ctk

from .animation import init_animation
from .constants import LABEL_SPRACHE, LABEL_GLAETTEN, WINDOW_WIDTH


def _tk_bind_key(key_str):
    """Hotkey-String fuer Tk bind: 'ctrl+y' -> 'Control-y'."""
    return key_str.replace("ctrl", "Control").replace("+", "-")


def _add_drag(window):
    """Fenster per Maus ziehen: ButtonPress speichert Offset, B1-Motion setzt geometry."""
    def start_drag(event):
        window._drag_data = {"x": event.x, "y": event.y}

    def on_drag(event):
        if hasattr(window, "_drag_data"):
            dx = event.x - window._drag_data["x"]
            dy = event.y - window._drag_data["y"]
            new_x = window.winfo_x() + dx
            new_y = window.winfo_y() + dy
            window.geometry(f"+{new_x}+{new_y}")

    def stop_drag(event):
        if hasattr(window, "_drag_data"):
            del window._drag_data

    window.bind("<ButtonPress-1>", start_drag)
    window.bind("<B1-Motion>", on_drag)
    window.bind("<ButtonRelease-1>", stop_drag)


def create_status_window(callbacks, hotkeys, initial_state, refs):
    """
    Baut das komplette Fenster: Top-Leiste (Animation, DE/EN, Transform-Switch, Minimal-Button),
    optional Button-/Bottom-Frames (Start, Stop, Mic, Tastatur, Beenden). Bindet hotkeys
    an callbacks. refs: window, lang_label, lang_switch_var, transform_text_var,
    keyboard_button, button_frame, bottom_frame, content_frame, top_frame.
    """
    is_minimal = initial_state.get("is_minimal_mode", True)
    transform_enabled = initial_state.get("transform_text_enabled", False)
    lang_label_text = "DE" if initial_state.get("current_language", "de") == "de" else "EN"

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    win = ctk.CTk()
    win.title("Spracherkennung")

    width = WINDOW_WIDTH
    height = 40 if is_minimal else 120
    win.geometry(f"{width}x{height}")
    win.attributes("-topmost", True)
    win.overrideredirect(True)
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    win.geometry(f"{width}x{height}+{(sw - width) // 2}+{(sh - height) // 2}")

    main_frame = ctk.CTkFrame(win, corner_radius=15, fg_color="#333333", border_width=0)
    main_frame.pack(fill="both", expand=True, padx=0, pady=0)
    content_frame = ctk.CTkFrame(main_frame, corner_radius=12, fg_color="#333333", border_width=0)
    content_frame.pack(fill="both", expand=True, padx=5, pady=5)

    button_bg = "#1E88E5"
    top_frame = ctk.CTkFrame(content_frame, corner_radius=0, fg_color="transparent")
    top_frame.pack(pady=2)

    # Animation: 7 Balken auf Canvas; ui.animation steuert Farbwechsel (start/stop von aussen)
    anim_frame = ctk.CTkFrame(top_frame, corner_radius=0, fg_color="transparent")
    anim_frame.grid(row=0, column=0, padx=2)
    heights = [12, 16, 20, 24, 20, 16, 12]
    cw, ch = 100, 24
    canvas = ctk.CTkCanvas(anim_frame, width=cw, height=ch, bg="#333333", highlightthickness=0)
    canvas.pack()
    bar_width, bar_spacing = 6, 6
    total_bars = (len(heights) * bar_width) + ((len(heights) - 1) * bar_spacing)
    start_x = (cw - total_bars) / 2
    bar_ids = []
    for i in range(7):
        x_pos = start_x + i * (bar_width + bar_spacing)
        h = heights[i]
        y_pos = ch - h
        bid = canvas.create_rectangle(
            x_pos, y_pos, x_pos + bar_width, ch, fill="#555555", outline=""
        )
        bar_ids.append(bid)
    init_animation(win, canvas, bar_ids)

    # Sprache: Schalter + Anzeige DE/EN (erkennbar im Interface)
    lang_switch_var = ctk.StringVar(value=lang_label_text)
    lang_switch = ctk.CTkSwitch(
        top_frame, text=LABEL_SPRACHE, command=callbacks["toggle_language"],
        variable=lang_switch_var, onvalue="DE", offvalue="EN",
        width=80, height=20, switch_width=36, switch_height=18, corner_radius=10,
        progress_color=button_bg, font=("Arial", 9)
    )
    lang_switch.grid(row=0, column=1, padx=(4, 2))
    refs["lang_switch_var"] = lang_switch_var
    refs["lang_switch"] = lang_switch
    lang_label = ctk.CTkLabel(top_frame, text=lang_label_text, font=("Arial", 10, "bold"), text_color="#FFFFFF")
    lang_label.grid(row=0, column=2, padx=2)

    # Text glätten: Schalter mit erkennbarem Label
    transform_var = ctk.BooleanVar(value=transform_enabled)
    transform_switch = ctk.CTkSwitch(
        top_frame, text=LABEL_GLAETTEN, variable=transform_var, command=callbacks["toggle_transform_text"],
        onvalue=True, offvalue=False, width=72, height=20, switch_width=36, switch_height=18,
        corner_radius=10, progress_color="#00D100", font=("Arial", 9)
    )
    transform_switch.grid(row=0, column=3, padx=(4, 2))
    refs["transform_text_var"] = transform_var
    refs["transform_switch"] = transform_switch

    # Minimal-Modus: Button "-" blendet Button-/Bottom-Frame ein/aus (toggle_minimal_mode)
    minimal_btn = ctk.CTkButton(
        top_frame, text="-", command=callbacks["toggle_minimal_mode"],
        width=24, height=20, corner_radius=10, fg_color=button_bg, hover_color="#1976D2", font=("Arial", 10, "bold")
    )
    minimal_btn.grid(row=0, column=4, padx=3)

    # Hauptbuttons
    button_frame = ctk.CTkFrame(content_frame, corner_radius=0, fg_color="transparent")
    bw, bh = 65, 28
    record_btn = ctk.CTkButton(
        button_frame, text="Start", command=callbacks["start_recording"],
        corner_radius=10, height=bh, width=bw, fg_color=button_bg, hover_color="#1976D2"
    )
    record_btn.grid(row=0, column=0, padx=2)
    stop_btn = ctk.CTkButton(
        button_frame, text="Stop", command=callbacks["stop_recording"],
        corner_radius=10, height=bh, width=bw, fg_color=button_bg, hover_color="#1976D2"
    )
    stop_btn.grid(row=0, column=1, padx=2)
    mic_btn = ctk.CTkButton(
        button_frame, text="Mic", command=callbacks["select_microphone"],
        corner_radius=10, height=bh, width=bw, fg_color=button_bg, hover_color="#1976D2"
    )
    mic_btn.grid(row=0, column=2, padx=2)

    bottom_frame = ctk.CTkFrame(content_frame, corner_radius=0, fg_color="transparent")
    kb_btn = ctk.CTkButton(
        bottom_frame, text="Tastatur: An", command=callbacks["toggle_keyboard"],
        corner_radius=10, height=24, width=110, fg_color=button_bg, hover_color="#1976D2"
    )
    kb_btn.grid(row=0, column=0, padx=2)
    settings_btn = ctk.CTkButton(
        bottom_frame, text="Einstellungen", command=callbacks["open_settings"],
        corner_radius=10, height=24, width=90, fg_color=button_bg, hover_color="#1976D2"
    )
    settings_btn.grid(row=0, column=1, padx=2)
    quit_btn = ctk.CTkButton(
        bottom_frame, text="Beenden", command=callbacks["quit_app"],
        corner_radius=10, height=24, width=60, fg_color="#E53935", hover_color="#C62828"
    )
    quit_btn.grid(row=0, column=2, padx=2)

    _add_drag(win)

    # Im Minimal-Modus Frames nicht packen (oder pack_forget), sonst unter top_frame packen
    if is_minimal:
        button_frame.pack_forget()
        bottom_frame.pack_forget()
    else:
        button_frame.pack(pady=2)
        bottom_frame.pack(pady=2)

    # Tk-Bindings: hotkeys["start_stop"] -> start_stop_toggle, rest -> jeweiliger Callback
    sk = _tk_bind_key(hotkeys.get("start_stop", "ctrl+y"))
    win.bind(f"<{sk}>", lambda e: callbacks["start_stop_toggle"]())
    for bind_name, cb_key in [
        ("toggle_language", "toggle_language"),
        ("toggle_keyboard", "toggle_keyboard"),
        ("quit", "quit_app"),
    ]:
        k = hotkeys.get(bind_name)
        if k:
            win.bind(f"<{_tk_bind_key(k)}>", lambda e, c=callbacks[cb_key]: c())

    refs["window"] = win
    refs["lang_label"] = lang_label
    refs["keyboard_button"] = kb_btn
    refs["button_frame"] = button_frame
    refs["bottom_frame"] = bottom_frame
    refs["content_frame"] = content_frame
    refs["top_frame"] = top_frame

    win.focus_force()
    win.lift()
    win.update()
    return win
