# =============================================================================
# UI/ANIMATION.PY – Wellen-Animation (Aufnahme / Transkription)
# =============================================================================
# Thread-sicher: start/stop koennen aus Hintergrund-Threads aufgerufen werden.
# Alle Canvas-Operationen laufen im Haupt-Thread via window.after(0, ...).
# _generation invalidiert veraltete after-Callbacks bei Richtungswechsel/Stop.
# =============================================================================

_bar_ids = []
_canvas = None
_window = None
_running = False
_mode = "idle"   # "wave" | "reverse" | "idle"
_generation = 0

COLORS = ["#555555", "#777777", "#999999", "#BBBBBB", "#DDDDDD", "#FFFFFF"]
_COLOR_IDLE = "#555555"


def init_animation(window, canvas, bar_ids):
    """Muss einmal aufgerufen werden (von window.py): Referenzen fuer after/itemconfig."""
    global _window, _canvas, _bar_ids
    _window = window
    _canvas = canvas
    _bar_ids = bar_ids


def _run_frame(step, gen):
    """
    Ein Frame der Animation – laeuft immer im Haupt-Thread (nur via window.after geplant).
    gen: Generation-Zaehler. Veraltete Callbacks (nach stop/restart) erkennen gen != _generation
    und brechen sofort ab, ohne weiteren after zu planen.
    """
    if gen != _generation or not _running or _mode == "idle":
        return
    if not _window or not _canvas or not _bar_ids:
        return
    n = len(_bar_ids)
    for i in range(n):
        if _mode == "wave":
            pos = (step + i) % len(COLORS)
        else:
            pos = (step + (n - 1 - i)) % len(COLORS)
        _canvas.itemconfig(_bar_ids[i], fill=COLORS[pos])
    _window.after(150, _run_frame, (step + 1) % len(COLORS), gen)


def _reset_bars_on_main():
    """Setzt alle Balken auf Ruhefarbe. Nur im Haupt-Thread (via after) aufrufen."""
    if _canvas and _bar_ids:
        for bid in _bar_ids:
            _canvas.itemconfig(bid, fill=_COLOR_IDLE)


def start_wave_animation():
    """Thread-sicher. Startet Wellen-Animation links-nach-rechts (Aufnahme laeuft)."""
    global _running, _mode, _generation
    if _running and _mode == "wave":
        return
    _running = True
    _mode = "wave"
    _generation += 1
    g = _generation
    if _window:
        _window.after(0, lambda: _run_frame(0, g))


def stop_wave_animation():
    """Thread-sicher. Stoppt Animation sofort, setzt Balken auf Ruhefarbe."""
    global _running, _mode, _generation
    _running = False
    _mode = "idle"
    _generation += 1
    if _window:
        _window.after(0, _reset_bars_on_main)


def start_reverse_animation():
    """Thread-sicher. Startet Rueckwaerts-Animation rechts-nach-links (Transkription laeuft)."""
    global _running, _mode, _generation
    if _running and _mode == "reverse":
        return
    _running = True
    _mode = "reverse"
    _generation += 1
    g = _generation
    if _window:
        _window.after(0, lambda: _run_frame(0, g))
