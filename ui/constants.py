# UI-Labels and size (no CTk import, for tests and consistency)
LABEL_SPRACHE = "Language"
LABEL_GLAETTEN = "Smooth"

# --- Fenster: Breiten und Hoehen pro Modus ---
# Ausgeklappter Modus (i-Button inaktiv): volle Breite mit Labels und Settings
WINDOW_WIDTH = 350
# Kompakt-Modus (i-Button aktiv): minimale Abstaende; nur Balken, Switch, Switch, i-Button
WINDOW_WIDTH_COMPACT = 210
WINDOW_HEIGHT_EXPANDED = 455
WINDOW_HEIGHT_COMPACT = 40
# Log-Bereich im ausgeklappten Modus (Hoehe in Pixeln; Fenster vergroessert sich nach unten)
LOG_AREA_HEIGHT = 230
# Kompakt: gleicher Abstand oben/unten (zentriert die Zeile vertikal)
COMPACT_PADY = 8

# --- Skalierungs-Multiplikatoren (Proportionen bleiben gleich) ---
# Balken-Animation: Canvas, Balkenhoehen, bar_width, bar_spacing
ANIM_SCALE = 0.8
# Switches (Language, Glaetten): width, height, switch_width, switch_height, Font, Trennstrich-Hoehe
SWITCH_SCALE = 0.9
# i-Button: Kreis (width, height, corner_radius)
INFO_BTN_SCALE = 0.9
# i-Button: Schriftgroesse des "i"
INFO_BTN_FONT_SCALE = 1.1

# i-Button: "inaktiv" (ausgeklappt) = dunkelgrau wie Switch-Hintergrund, "aktiv" (kompakt) = gleicher Hintergrund.
# Die Textfarbe wird getrennt in window.py gesteuert.
INFO_BTN_BG = "#4A4D50"
INFO_BTN_BG_HOVER = "#5C5F62"
INFO_BTN_TEXT_COLOR = "#1E88E5"
