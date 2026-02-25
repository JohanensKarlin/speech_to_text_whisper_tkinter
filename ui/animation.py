# =============================================================================
# UI/ANIMATION.PY – Wellen-Animation (Aufnahme / Transkription)
# =============================================================================
# Modul-State: _window, _canvas, _bar_ids (von init_animation gesetzt). Animation
# laeuft ueber window.after(150, ...) in Schleife. start_wave = links-nach-rechts,
# start_reverse = rechts-nach-links. Aufrufer: speech_to_text.process_recording.
# =============================================================================

_bar_ids = []
_canvas = None
_window = None
_running = False
_after_id = None

# Farbfolge fuer die Balken (dunkel -> hell)
COLORS = ["#555555", "#777777", "#999999", "#BBBBBB", "#DDDDDD", "#FFFFFF"]


def init_animation(window, canvas, bar_ids):
    """Muss einmal aufgerufen werden (von window.py): Referenzen fuer after/itemconfig."""
    global _window, _canvas, _bar_ids
    _window = window
    _canvas = canvas
    _bar_ids = bar_ids


def _run_wave(step):
    """Ein Frame: Balken i bekommt Farbe (step+i) % len(COLORS); naechster Aufruf in 150 ms."""
    global _running, _after_id
    if not _running or not _window or not _canvas or not _bar_ids:
        return
    n = len(_bar_ids)
    for i in range(n):
        pos = (step + i) % len(COLORS)
        _canvas.itemconfig(_bar_ids[i], fill=COLORS[pos])
    _after_id = _window.after(150, _run_wave, (step + 1) % len(COLORS))


def _run_reverse(step):
    """Wie _run_wave, aber Laufrichtung rechts-nach-links (Index n-1-i)."""
    global _running, _after_id
    if not _running or not _window or not _canvas or not _bar_ids:
        return
    n = len(_bar_ids)
    for i in range(n):
        pos = (step + (n - 1 - i)) % len(COLORS)
        _canvas.itemconfig(_bar_ids[i], fill=COLORS[pos])
    _after_id = _window.after(150, _run_reverse, (step + 1) % len(COLORS))


def start_wave_animation():
    """Startet Wellen-Animation (Aufnahme). Idempotent: wenn schon _running, kein neuer after."""
    global _running, _after_id
    if _running:
        return
    _running = True
    _run_wave(0)


def stop_wave_animation():
    """Stoppt Animation, cancelt pending after, setzt alle Balken auf Ruhefarbe."""
    global _running, _after_id
    _running = False
    if _window and _after_id is not None:
        _window.after_cancel(_after_id)
        _after_id = None
    if _canvas and _bar_ids:
        for bid in _bar_ids:
            _canvas.itemconfig(bid, fill="#555555")


def start_reverse_animation():
    """Startet Rueckwaerts-Animation (Transkription laeuft). Idempotent wie start_wave."""
    global _running
    if _running:
        return
    _running = True
    _run_reverse(0)
