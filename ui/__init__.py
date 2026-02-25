# ui – Fensteraufbau (create_status_window), Wellen-Animation, Dialog-Platzierung.
# Keine App-Logik; Callbacks und State kommen von speech_to_text.
from .animation import init_animation, start_wave_animation, stop_wave_animation, start_reverse_animation
from .constants import LABEL_SPRACHE, LABEL_GLAETTEN, WINDOW_WIDTH
from .placement import get_dialog_position_beside_parent
from .window import create_status_window

__all__ = [
    "init_animation",
    "start_wave_animation",
    "stop_wave_animation",
    "start_reverse_animation",
    "create_status_window",
    "get_dialog_position_beside_parent",
    "LABEL_SPRACHE",
    "LABEL_GLAETTEN",
    "WINDOW_WIDTH",
]
