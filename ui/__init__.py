# ui – Fensteraufbau (create_status_window) und Wellen-Animation (init + start/stop_wave, start_reverse).
# Keine App-Logik; Callbacks und State kommen von speech_to_text.
from .animation import init_animation, start_wave_animation, stop_wave_animation, start_reverse_animation
from .constants import LABEL_SPRACHE, LABEL_GLAETTEN, WINDOW_WIDTH
from .window import create_status_window

__all__ = [
    "init_animation",
    "start_wave_animation",
    "stop_wave_animation",
    "start_reverse_animation",
    "create_status_window",
    "LABEL_SPRACHE",
    "LABEL_GLAETTEN",
    "WINDOW_WIDTH",
]
