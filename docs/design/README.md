# Design – Statusfenster UX/UI (Experten-Referenz)

Dieses Dokument beschreibt das Layout des schwebenden Speech-Recognition-Fensters exakt. Nutze es, um in Gespraechen oder neuen Sessions sofort auf Experten-Level einzusteigen: ASCII-Skizzen, Spaltenzuordnung zum Code, und zwei Zustaende (Kompakt / Ausgeklappt).

---

## 1. Zwei Zustaende

Es gibt strikt nur zwei Modi. Umschaltung erfolgt ueber den "[ i ]" Button (`toggle_info_compact`).

| Zustand   | Hoehe | Sichtbar | Breite |
|-----------|-------|----------|--------|
| Kompakt   | 40 px  | Nur Top-Leiste, ohne Textlabels | `WINDOW_WIDTH_COMPACT` |
| Ausgeklappt | 120 px | Top-Leiste (mit Texten) + Button-Frames | `WINDOW_WIDTH` |

---

## 2. Top-Leiste (top_frame) – Eine Zeile, Grid

Reihenfolge von links nach rechts:

1. **Animation** (7 Balken)
2. **Language:** Switch (Text "Language" im ausgeklappten Modus)
3. **Aktuelle Sprache:** DE oder EN
4. **Smooth:** Switch (Text "Smooth" im ausgeklappten Modus)
5. **Vertikaler Trennstrich** (sep) – Nur sichtbar im ausgeklappten Modus
6. **Info-Button** "[ i ]" – Togglet zwischen Kompakt und Ausgeklappt

---

## 3. ASCII – Kompakt-Modus (Startzustand)

```
+------------------------------------------+
|  +------------------------------------+  |
|  |  [ ||||||| ]  (o)   (o)   [ i ]  |  |
|  |    col 0      col1  col4  col6  |  |
|  |    Balken    Switch Switch i   |  |
|  |  Vier Elemente; "Language"/"Smooth" und DE/EN weg. |  |
|  |  i-Button hellgrau (inaktiv).         |  |
|  +------------------------------------+  |
+------------------------------------------+
```
_Kein sep. Breite: WINDOW_WIDTH_COMPACT_

---

## 4. ASCII – Ausgeklappt (Top + Button-Zeilen)

```
+----------------------------------------------------------------------------------------------------------+
|  +----------------------------------------------------------------------------------------------------+  |
|  |    [ ||||||| ]     (o----)  Language   DE      |      (o----)  Smooth      |     [ i ]              |  |
|  |      col 0         col 1      col 2           col 3   col 4               col 5  col 6              |  |
|  +----------------------------------------------------------------------------------------------------+  |
|  |  [ Start ]   [ Stop ]   [ Keyboard: On ]                                                             |  |
|  |  button_frame: record_btn, stop_btn, kb_btn                                                            |  |
|  +----------------------------------------------------------------------------------------------------+  |
|  |  [ Smoothing ]   [ API ]   [ Keys ]   [ Quit ]                                                        |  |
|  |  bottom_frame: smooth_btn, api_btn, keys_btn, quit_btn                                                |  |
|  +----------------------------------------------------------------------------------------------------+  |
+----------------------------------------------------------------------------------------------------------+
```

---

## 5. Spaltenzuordnung Top-Leiste <-> Code (window.py)

| Grid column | Widget / Inhalt        | Code-Referenz |
|-------------|------------------------|----------------|
| 0           | 7 Balken (Animation)   | `anim_frame`, darin `canvas` + `bar_ids`; `init_animation(win, canvas, bar_ids)` |
| 1           | Language-Switch        | `lang_switch` (CTkSwitch, text=LABEL_SPRACHE oder "", onvalue "DE", offvalue "EN") |
| 2           | Aktuelle Sprache DE/EN | `lang_label` (CTkLabel); Callbacks aendern Text ueber refs["lang_label"] |
| 3           | Trennstrich            | `sep` (2px breit, 22px hoch) – wird in Kompakt aus dem Grid entfernt |
| 4           | Smooth-Switch          | `transform_switch` (CTkSwitch, text=LABEL_GLAETTEN oder "") |
| 6           | Info-Button            | `info_btn` (Text "i", command=toggle_info_compact); immer selbe Farbe, Text blau |

Alle in **top_frame**, **row=0**; Layout: `grid(row=0, column=N, ...)`.
_(Column 5 ist aktuell ungenutzt, da sep2 und minimal_btn entfernt wurden)_

---

## 6. Frames und refs (fuer Callbacks)

- **top_frame:** Immer sichtbar; enthaelt Animation, Switches, Label, Separator, Info-Button.
- **button_frame:** Nur aufgeklappt; Start, Stop, Keyboard-Button.
- **bottom_frame:** Nur aufgeklappt; Smoothing, API, Keys, Quit.

Refs fuer Kompakt-Toggle: `anim_frame`, `lang_switch`, `lang_label`, `transform_switch`, `sep`, `info_btn`, `button_frame`, `bottom_frame`, `content_frame`, `top_frame`.

Callbacks in `speech_to_text.py` bekommen `refs` und koennen z.B.:
- `toggle_info_compact`: schaltet Text der Switches an/aus, passt Padding (padx/pady) an, zeigt/versteckt `sep` und die beiden unteren Frames, aendert Fenstergroesse.

---

## 7. Wiedereinstieg auf Experten-Level

- **Layout aendern:** Nur Top-Leiste -> Spalten in `window.py` (grid column 0..6) und diese Sektion 5.
- **Zwei Modi aendern:** `toggle_info_compact` in `speech_to_text.py` steuert das komplette Layout-Wechselspiel inkl. Pad-Anpassungen.
- **Labels/Farben:** `ui/constants.py` (LABEL_SPRACHE, LABEL_GLAETTEN, WINDOW_WIDTH, WINDOW_WIDTH_COMPACT, INFO_BTN_BG, INFO_BTN_TEXT_COLOR).

