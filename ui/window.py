# =============================================================================
# UI/WINDOW.PY – Schwebendes Statusfenster (nur Aufbau, keine Logik)
# =============================================================================
# Erstellt CTk-Fenster, Frames, Buttons, Switches, Animation-Canvas. Alle Aktionen
# ueber callbacks (von speech_to_text.py). refs wird mit window, lang_label,
# transform_text_var, button_frame, etc. befuellt, damit Callbacks die UI updaten.
# =============================================================================

import sys
import pyperclip
import customtkinter as ctk

from .animation import init_animation


def _create_chat_bubble(parent, text, bubble_type="system"):
    """
    Erstellt eine ChatBubble mit Text und Copy-Button.
    bubble_type: "transcript" (blau) oder "error" (rot)
    """
    bubble_colors = {
        "transcript": {"bg": "#1E88E5", "text": "#FFFFFF"},
        "error": {"bg": "#E53935", "text": "#FFFFFF"},
    }
    if bubble_type not in bubble_colors:
        return None
    colors = bubble_colors[bubble_type]
    original_color = colors["bg"]

    bubble_frame = ctk.CTkFrame(
        parent, corner_radius=8, fg_color=colors["bg"], border_width=0
    )

    def copy_text():
        pyperclip.copy(text)
        bubble_frame.configure(fg_color="#2E7D32")
        bubble_frame.after(300, lambda: bubble_frame.configure(fg_color=original_color))

    copy_btn = ctk.CTkButton(
        bubble_frame,
        text="Copy",
        command=copy_text,
        width=50,
        height=20,
        corner_radius=4,
        fg_color="#555555",
        hover_color="#666666",
        font=("Arial", 8),
    )
    copy_btn.pack(side="bottom", anchor="se", padx=4, pady=4)

    text_label = ctk.CTkLabel(
        bubble_frame,
        text=text,
        font=("Consolas", 10),
        text_color=colors["text"],
        wraplength=280,
        justify="left",
    )
    text_label.pack(fill="x", padx=8, pady=(6, 0))

    return bubble_frame


from .constants import (
    LABEL_SPRACHE,
    LABEL_GLAETTEN,
    WINDOW_WIDTH,
    WINDOW_WIDTH_COMPACT,
    WINDOW_HEIGHT_COMPACT,
    WINDOW_HEIGHT_EXPANDED,
    COMPACT_PADY,
    LOG_AREA_HEIGHT,
    ANIM_SCALE,
    SWITCH_SCALE,
    INFO_BTN_SCALE,
    INFO_BTN_FONT_SCALE,
    INFO_BTN_BG,
    INFO_BTN_BG_HOVER,
    INFO_BTN_TEXT_COLOR,
)


def _tk_bind_key(key_str):
    """Hotkey-String fuer Tk bind: 'ctrl+y' -> 'Control-y', 'alt+l' -> 'Alt-l' (Keysyms case-sensitive unter Windows)."""
    s = (key_str or "").strip().lower()
    s = s.replace("ctrl", "Control").replace("alt", "Alt").replace("+", "-")
    return s


def _add_drag(window):
    """Fenster per Maus ziehen: ButtonPress speichert Offset, B1-Motion setzt geometry.
    Text- und Entry-Widgets werden ausgespart, damit Textauswahl/Kopieren funktioniert."""
    _no_drag_classes = {
        "Text",
        "Entry",
        "TEntry",
        "Button",
        "TButton",
        "Scale",
        "TScale",
        "Scrollbar",
        "TCombobox",
        "Listbox",
        "Spinbox",
        "Canvas",
    }

    def _is_interactive_widget(widget):
        w = widget
        while w is not None:
            try:
                if w.winfo_class() in _no_drag_classes:
                    return True
                if w == window:
                    return False
                w = w.master
            except Exception:
                return True
        return False

    def start_drag(event):
        if _is_interactive_widget(event.widget):
            return
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


def _set_taskbar_visible(window):
    """
    Fenster in der Windows-Taskleiste anzeigen, damit es unten bei allen Programmen
    sichtbar ist und per Klick wieder in den Vordergrund geholt werden kann.
    Nur unter Windows; bei overrideredirect sonst oft nicht in der Taskleiste.
    """
    if sys.platform != "win32":
        return
    try:
        from ctypes import windll

        GWL_EXSTYLE = -20
        WS_EX_APPWINDOW = 0x00040000
        WS_EX_TOOLWINDOW = 0x00000080
        hwnd = windll.user32.GetParent(window.winfo_id())
        if not hwnd:
            return
        style = windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        style = (style & ~WS_EX_TOOLWINDOW) | WS_EX_APPWINDOW
        windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        window.wm_withdraw()
        window.after(10, lambda: window.wm_deiconify())
    except Exception:
        pass


def create_status_window(callbacks, hotkeys, initial_state, refs):
    """
    Baut das komplette Fenster: Top-Leiste (Animation, DE/EN, Transform-Switch, Minimal-Button),
    optional Button-/Bottom-Frames (Start, Stop, Mic, Tastatur, Beenden). Bindet hotkeys
    an callbacks. refs: window, lang_label, lang_switch_var, transform_text_var,
    keyboard_button, button_frame, bottom_frame, content_frame, top_frame.
    """
    is_minimal = initial_state.get("is_minimal_mode", True)
    transform_enabled = initial_state.get("transform_text_enabled", False)
    lang_label_text = (
        "DE" if initial_state.get("current_language", "de") == "de" else "EN"
    )
    top_bar_compact = initial_state.get("top_bar_compact", False)

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    win = ctk.CTk()
    win.title("Speech Recognition")

    width = WINDOW_WIDTH
    height = WINDOW_HEIGHT_COMPACT if is_minimal else WINDOW_HEIGHT_EXPANDED
    win.geometry(f"{width}x{height}")
    win.attributes("-topmost", True)
    win.overrideredirect(True)
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    win.geometry(f"{width}x{height}+{(sw - width) // 2}+{(sh - height) // 2}")

    main_frame = ctk.CTkFrame(win, corner_radius=15, fg_color="#333333", border_width=0)
    main_frame.pack(fill="both", expand=True, padx=0, pady=0)
    content_frame = ctk.CTkFrame(
        main_frame, corner_radius=12, fg_color="#333333", border_width=0
    )
    # Kompakt: padx=0, symmetrisches pady (COMPACT_PADY oben/unten), Top-Zeile zentriert
    compact_padx = 0 if top_bar_compact else 5
    compact_pady = (COMPACT_PADY, COMPACT_PADY) if top_bar_compact else 5
    content_frame.pack(fill="both", expand=True, padx=compact_padx, pady=compact_pady)

    # Wrapper nimmt volle Breite; top_frame darin zentriert (links/rechts gleich)
    center_wrapper = ctk.CTkFrame(
        content_frame, corner_radius=0, fg_color="transparent"
    )
    center_wrapper.pack(fill="both", expand=True)

    button_bg = "#1E88E5"
    top_frame = ctk.CTkFrame(center_wrapper, corner_radius=0, fg_color="transparent")
    # Kompakt: anchor="center" damit Balken+Switches+i horizontal zentriert; vertikal pady=0
    top_frame.pack(
        pady=0 if top_bar_compact else 2, anchor="center" if top_bar_compact else "n"
    )

    # Animation: 7 Balken auf Canvas; ui.animation steuert Farbwechsel (start/stop von aussen)
    # Alle Masse mit ANIM_SCALE (Proportionen bleiben gleich)
    anim_frame = ctk.CTkFrame(top_frame, corner_radius=0, fg_color="transparent")
    anim_frame.grid(row=0, column=0, padx=2)
    _base_heights = [12, 16, 20, 24, 20, 16, 12]
    heights = [max(1, int(h * ANIM_SCALE)) for h in _base_heights]
    cw = max(20, int(100 * ANIM_SCALE))
    ch = max(8, int(24 * ANIM_SCALE))
    canvas = ctk.CTkCanvas(
        anim_frame, width=cw, height=ch, bg="#333333", highlightthickness=0
    )
    canvas.pack()
    bar_width = bar_spacing = max(1, int(6 * ANIM_SCALE))
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

    # Sprache: Schalter + Anzeige DE/EN (erkennbar im Interface); SWITCH_SCALE fuer alle Masse
    _sw_w, _sw_h = max(20, int(84 * SWITCH_SCALE)), max(14, int(22 * SWITCH_SCALE))
    _sw_sw, _sw_sh = max(20, int(38 * SWITCH_SCALE)), max(12, int(18 * SWITCH_SCALE))
    _sw_cr = max(4, int(10 * SWITCH_SCALE))
    _sw_font = max(8, int(10 * SWITCH_SCALE))
    lang_switch_var = ctk.StringVar(value=lang_label_text)
    lang_switch = ctk.CTkSwitch(
        top_frame,
        text=LABEL_SPRACHE,
        command=callbacks["toggle_language"],
        variable=lang_switch_var,
        onvalue="DE",
        offvalue="EN",
        width=_sw_w,
        height=_sw_h,
        switch_width=_sw_sw,
        switch_height=_sw_sh,
        corner_radius=_sw_cr,
        progress_color=button_bg,
        font=("Arial", _sw_font),
    )
    lang_switch.grid(row=0, column=1, padx=(6, 4))
    refs["lang_switch_var"] = lang_switch_var
    refs["lang_switch"] = lang_switch
    _label_font = max(9, int(11 * SWITCH_SCALE))
    lang_label = ctk.CTkLabel(
        top_frame,
        text=lang_label_text,
        font=("Arial", _label_font, "bold"),
        text_color="#FFFFFF",
    )
    lang_label.grid(row=0, column=2, padx=4)

    # Vertikaler Trennstrich zwischen Sprache und Glaetten (Hilfe fuer das Auge); Hoehe wie Switch
    sep = ctk.CTkFrame(
        top_frame, width=2, height=_sw_h, fg_color="#FFFFFF", corner_radius=0
    )
    sep.grid(row=0, column=3, padx=8, pady=2)
    sep.grid_propagate(False)

    # Text glaetten: Schalter mit erkennbarem Label (SWITCH_SCALE)
    _tw = max(20, int(76 * SWITCH_SCALE))
    transform_var = ctk.BooleanVar(value=transform_enabled)
    transform_switch = ctk.CTkSwitch(
        top_frame,
        text=LABEL_GLAETTEN,
        variable=transform_var,
        command=callbacks["toggle_transform_text"],
        onvalue=True,
        offvalue=False,
        width=_tw,
        height=_sw_h,
        switch_width=_sw_sw,
        switch_height=_sw_sh,
        corner_radius=_sw_cr,
        progress_color="#00D100",
        font=("Arial", _sw_font),
    )
    transform_switch.grid(row=0, column=4, padx=(4, 2))
    refs["transform_text_var"] = transform_var
    refs["transform_switch"] = transform_switch

    # Info-Kompakt (nur noch dieser Toggle): Button "i" faehrt Top-Leiste zusammen und versteckt Bottom-Frames.
    # INFO_BTN_SCALE fuer Kreis, INFO_BTN_FONT_SCALE fuer "i"
    _ib_sz = max(12, int(18 * INFO_BTN_SCALE))
    _ib_cr = max(4, int(9 * INFO_BTN_SCALE))
    _ib_font = max(8, int(11 * INFO_BTN_FONT_SCALE))
    info_btn_fg = INFO_BTN_BG if top_bar_compact else INFO_BTN_BG
    info_btn = ctk.CTkButton(
        top_frame,
        text="i",
        command=callbacks["toggle_info_compact"],
        width=_ib_sz,
        height=_ib_sz,
        corner_radius=_ib_cr,
        fg_color=info_btn_fg,
        hover_color=INFO_BTN_BG_HOVER,
        text_color=INFO_BTN_TEXT_COLOR,
        font=("Arial", _ib_font, "bold"),
    )
    info_btn.grid(row=0, column=6, padx=(2, 4))

    # Zeile 1: Start, Stop, Keyboard (links)
    button_frame = ctk.CTkFrame(center_wrapper, corner_radius=0, fg_color="transparent")
    bw, bh = 65, 28
    record_btn = ctk.CTkButton(
        button_frame,
        text="Start",
        command=callbacks["start_recording"],
        corner_radius=10,
        height=bh,
        width=bw,
        fg_color=button_bg,
        hover_color="#1976D2",
    )
    record_btn.grid(row=0, column=0, padx=2)
    stop_btn = ctk.CTkButton(
        button_frame,
        text="Stop",
        command=callbacks["stop_recording"],
        corner_radius=10,
        height=bh,
        width=bw,
        fg_color=button_bg,
        hover_color="#1976D2",
    )
    stop_btn.grid(row=0, column=1, padx=2)
    kb_initial = (
        "Keyboard: On"
        if initial_state.get("keyboard_enabled", True)
        else "Keyboard: Off"
    )
    kb_btn = ctk.CTkButton(
        button_frame,
        text=kb_initial,
        command=callbacks["toggle_keyboard"],
        corner_radius=10,
        height=bh,
        width=100,
        fg_color=button_bg,
        hover_color="#1976D2",
    )
    kb_btn.grid(row=0, column=2, padx=2)

    # Zeile 1b: Mikrofon-Auswahl, Pegel und Gain
    mic_frame = ctk.CTkFrame(center_wrapper, corner_radius=8, fg_color="#2d2d2d")
    ctk.CTkLabel(
        mic_frame,
        text="Mic",
        font=("Arial", 11, "bold"),
        text_color="#E0E0E0",
    ).grid(row=0, column=0, padx=(8, 6), pady=(6, 2), sticky="w")

    mic_values = initial_state.get("microphone_names", ["Default-Mikrofon"])
    mic_var = ctk.StringVar(value=(mic_values[0] if mic_values else "Default-Mikrofon"))
    mic_combo = ctk.CTkComboBox(
        mic_frame,
        values=mic_values,
        variable=mic_var,
        width=220,
        height=28,
        font=("Arial", 11),
        command=lambda selected: callbacks["select_microphone"](selected),
    )
    mic_combo.grid(row=0, column=1, padx=(0, 8), pady=(6, 2), sticky="w")

    ctk.CTkLabel(
        mic_frame,
        text="Input",
        font=("Arial", 10),
        text_color="#AFAFAF",
    ).grid(row=1, column=0, padx=(8, 6), pady=(0, 6), sticky="w")
    level_progress = ctk.CTkProgressBar(
        mic_frame,
        width=190,
        height=12,
        progress_color="#00D26A",
    )
    level_progress.set(0.0)
    level_progress.grid(row=1, column=1, padx=(0, 6), pady=(0, 6), sticky="w")

    gain_val = float(initial_state.get("microphone_gain", 1.0))
    gain_steps_val = int(round(gain_val * 10.0))
    gain_var = ctk.IntVar(value=max(5, min(30, gain_steps_val)))
    gain_label = ctk.CTkLabel(
        mic_frame,
        text=f"Gain {gain_val:.1f}x",
        font=("Arial", 10),
        text_color="#AFAFAF",
    )
    gain_label.grid(row=1, column=2, padx=(0, 4), pady=(0, 6), sticky="w")

    def _on_gain_change(value):
        try:
            v = float(value) / 10.0
        except Exception:
            v = 1.0
        gain_label.configure(text=f"Gain {v:.1f}x")
        callbacks["set_microphone_gain"](v)

    gain_slider = ctk.CTkSlider(
        mic_frame,
        from_=5,
        to=30,
        number_of_steps=25,
        variable=gain_var,
        width=90,
        command=_on_gain_change,
    )
    gain_slider.grid(row=1, column=3, padx=(0, 4), pady=(0, 6), sticky="w")

    # Zeile 2: Smoothing, API, Keys, Quit (links)
    bottom_frame = ctk.CTkFrame(center_wrapper, corner_radius=0, fg_color="transparent")
    smooth_btn = ctk.CTkButton(
        bottom_frame,
        text="Smoothing",
        command=callbacks["open_smoothing"],
        corner_radius=10,
        height=24,
        width=85,
        fg_color=button_bg,
        hover_color="#1976D2",
    )
    smooth_btn.grid(row=0, column=0, padx=2)
    api_btn = ctk.CTkButton(
        bottom_frame,
        text="API",
        command=callbacks["open_api"],
        corner_radius=10,
        height=24,
        width=60,
        fg_color=button_bg,
        hover_color="#1976D2",
    )
    api_btn.grid(row=0, column=1, padx=2)
    keys_btn = ctk.CTkButton(
        bottom_frame,
        text="Keys",
        command=callbacks["open_keys"],
        corner_radius=10,
        height=24,
        width=55,
        fg_color=button_bg,
        hover_color="#1976D2",
    )
    keys_btn.grid(row=0, column=2, padx=2)
    quit_btn = ctk.CTkButton(
        bottom_frame,
        text="Quit",
        command=callbacks["quit_app"],
        corner_radius=10,
        height=24,
        width=60,
        fg_color="#E53935",
        hover_color="#C62828",
    )
    quit_btn.grid(row=0, column=3, padx=2)

    # Log-Bereich (nur ausgeklappt): Chat-Bubbles (scrollbar)
    log_frame = ctk.CTkFrame(
        center_wrapper, corner_radius=6, fg_color="#2a2a2a", border_width=1
    )
    log_scroll = ctk.CTkScrollableFrame(
        log_frame,
        height=LOG_AREA_HEIGHT,
        fg_color="#2a2a2a",
        scrollbar_button_color="#444444",
        scrollbar_button_hover_color="#555555",
    )
    log_scroll.pack(fill="both", expand=True, padx=4, pady=4)

    refs["log_scroll"] = log_scroll
    refs["chat_bubbles"] = []

    def add_chat_bubble(text, bubble_type="system"):
        """Fuegt eine ChatBubble hinzu und scrollt nach unten."""
        bubble = _create_chat_bubble(log_scroll, text, bubble_type)
        if bubble is None:
            return None
        bubble.pack(fill="x", pady=(0, 4))
        refs["chat_bubbles"].append(bubble)
        try:
            log_scroll._parent_canvas.yview_moveto(1.0)
        except Exception:
            pass
        return bubble

    refs["add_chat_bubble"] = add_chat_bubble

    log_text = None

    _add_drag(win)

    # Kompakt-Modus (i aktiv): nur Switch-Texte "Language"/"Smooth" weg; DE/EN bleibt. sep ausblenden.
    # Minimale Abstaende zwischen den fuenf Elementen (padx/width) fuer kompakte Ansicht.
    if top_bar_compact:
        lang_switch.configure(text="", width=_sw_sw)
        transform_switch.configure(text="", width=_sw_sw)
        sep.grid_remove()
        lang_label.grid_remove()
        anim_frame.grid_configure(padx=(4, 0))
        lang_switch.grid_configure(padx=(0, 2))
        transform_switch.grid_configure(padx=(0, 6))
        info_btn.grid_configure(padx=(0, 4))
        top_frame.pack_configure(pady=0, anchor="center")
        win.update_idletasks()
        wx, wy = win.winfo_x(), win.winfo_y()
        win.geometry(f"{WINDOW_WIDTH_COMPACT}x{WINDOW_HEIGHT_COMPACT}+{wx}+{wy}")

    # Im Kompakt-Modus nur top_frame; ausgeklappt: top_frame, button_frame, bottom_frame, log_frame
    if top_bar_compact:
        button_frame.pack_forget()
        mic_frame.pack_forget()
        bottom_frame.pack_forget()
        log_frame.pack_forget()
    else:
        button_frame.pack(pady=2, anchor="w")
        mic_frame.pack(pady=(2, 2), fill="x")
        bottom_frame.pack(pady=2, anchor="w")
        log_frame.pack(pady=4, fill="x")

    refs["log_frame"] = log_frame
    refs["log_text"] = log_text
    refs["log_scroll"] = log_scroll

    # Tk-Bindings: hotkeys["start_stop"] -> start_stop_toggle, rest -> jeweiliger Callback
    sk = _tk_bind_key(hotkeys.get("start_stop", "ctrl+y"))
    win.bind(f"<{sk}>", lambda e: callbacks["start_stop_toggle"]())
    refs["hotkey_start_stop_tk"] = sk
    for bind_name, cb_key in [
        ("toggle_language", "toggle_language"),
        ("toggle_keyboard", "toggle_keyboard"),
        ("quit", "quit_app"),
    ]:
        k = hotkeys.get(bind_name)
        if k:
            win.bind(f"<{_tk_bind_key(k)}>", lambda e, c=callbacks[cb_key]: c())

    refs["window"] = win
    refs["anim_frame"] = anim_frame
    refs["lang_label"] = lang_label
    refs["sep"] = sep
    refs["info_btn"] = info_btn
    refs["keyboard_button"] = kb_btn
    refs["button_frame"] = button_frame
    refs["mic_frame"] = mic_frame
    refs["mic_combo"] = mic_combo
    refs["mic_var"] = mic_var
    refs["level_progress"] = level_progress
    refs["gain_slider"] = gain_slider
    refs["bottom_frame"] = bottom_frame
    refs["content_frame"] = content_frame
    refs["top_frame"] = top_frame

    win.focus_force()
    win.lift()
    win.update()
    _set_taskbar_visible(win)
    return win
