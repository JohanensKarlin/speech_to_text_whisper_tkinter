# Design – Statusfenster UX/UI (Experten-Referenz)

Dieses Dokument beschreibt das Layout des schwebenden Speech-Recognition-Fensters exakt. Nutze es, um in Gespraechen oder neuen Sessions sofort auf Experten-Level einzusteigen: ASCII-Skizzen, Spaltenzuordnung zum Code, und zwei Zustaende (zugeklappt / aufgeklappt).

---

## 1. Zwei Zustaende

| Zustand   | Hoehe | Sichtbar |
|-----------|-------|----------|
| Zugeklappt (Minimal) | 40 px  | Nur Top-Leiste (eine Zeile). |
| Aufgeklappt          | 120 px | Top-Leiste + button_frame + bottom_frame. |

Umschaltung ueber den Minimal-Button "[ - ]" in der Top-Leiste; Callback `toggle_minimal_mode`. Im Code: `is_minimal` steuert `geometry` (height) und ob `button_frame`/`bottom_frame` per `pack` sichtbar oder per `pack_forget` ausgeblendet sind.

---

## 2. Top-Leiste (top_frame) – Eine Zeile, Grid

Reihenfolge von links nach rechts (so im Code und so gewuenscht):

1. **Animation** (7 Balken)
2. **Language:** Switch, dann Text-Label "Language", dann aktueller Wert **DE** oder **EN**
3. **Vertikaler Trennstrich** (sep)
4. **Smooth:** Switch, Label "Smooth" am Switch
5. **Vertikaler Trennstrich** (sep2)
6. **Minimal-Button** "[ - ]"
7. **Info-Button** "[ i ]" – Klick togglet Kompakt-Modus (siehe Abschnitt 2b)

### 2b. Kompakt-Modus (i-Button aktiv)

Aktivierung: Klick auf "[ i ]". Dann:
- Ansicht faehrt nach links zusammen; Fensterbreite wird **WINDOW_WIDTH_COMPACT** (z.B. 320).
- **Fuenf Elemente** sichtbar: **col 0** (Balken), **col 1** (Language-Switch), **col 2** (DE/EN-Indikator), **col 4** (Smooth-Switch), **col 7** (i-Button).
- Die **Texte "Language" und "Smooth"** an den Switches werden ausgeblendet (configure(text="")); der Indikator **DE** bzw. **EN** bleibt.
- Ausgeblendet: sep (col 3), sep2 (col 5), minimal_btn (col 6).
- Der i-Button wird **hellgrau** (INFO_BTN_COLOR_ACTIVE).

Erneuter Klick: Switch-Texte zurueck (LABEL_SPRACHE, LABEL_GLAETTEN), sep/minimal wieder sichtbar, Breite WINDOW_WIDTH, i blau. Callback: `toggle_info_compact`; State: `state["top_bar_compact"]`.

---

## 3. ASCII – Zugeklappt (nur Top-Leiste), Normalbreite

```
+----------------------------------------------------------------------------------------------------------+
|  +----------------------------------------------------------------------------------------------------+  |
|  |    [ ||||||| ]     (o----)  Language   DE      |      (o----)  Smooth      |     [ - ]   [ i ]      |  |
|  |      col 0         col 1      col 2           |       col 4               |     col 6    col 7      |  |
|  |                                               col 3   sep                 col 5  sep2   Info-Button |  |
|  +----------------------------------------------------------------------------------------------------+  |
+----------------------------------------------------------------------------------------------------------+
     Fensterbreite: WINDOW_WIDTH (z.B. 420). i-Button blau wenn inaktiv.
```

### 3b. ASCII – Kompakt-Modus (i-Button aktiv)

```
+------------------------------------------+
|  +------------------------------------+  |
|  |  [ ||||||| ]  (o)  DE  (o)   [ i ]  |  |
|  |    col 0      col1  col2  col4  col7  |  |
|  |    Balken    Switch DE/EN Switch i   |  |
|  |  Fuenf Elemente; "Language"/"Smooth"-Text an Switches weg. |  |
|  |  i-Button hellgrau (aktiv).         |  |
|  +------------------------------------+  |
+------------------------------------------+
```

---

## 4. ASCII – Aufgeklappt (Top + Button-Zeilen)

```
+----------------------------------------------------------------------------------------------------------+
|  +----------------------------------------------------------------------------------------------------+  |
|  |    [ ||||||| ]     (o----)  Language   DE      |      (o----)  Smooth      |     [ - ]   [ i ]      |  |
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
| 1           | Language-Switch        | `lang_switch` (CTkSwitch, text=LABEL_SPRACHE, onvalue "DE", offvalue "EN") |
| 2           | Aktuelle Sprache DE/EN | `lang_label` (CTkLabel); Callbacks aendern Text ueber refs["lang_label"] |
| 3           | Trennstrich            | `sep` (2px breit, 22px hoch) |
| 4           | Smooth-Switch          | `transform_switch` (CTkSwitch, text=LABEL_GLAETTEN); Variable refs["transform_text_var"] |
| 5           | Trennstrich            | `sep2` |
| 6           | Minimal-Button         | `minimal_btn` (Text "-", command=toggle_minimal_mode) |
| 7           | Info-Button            | `info_btn` (Text "i", command=toggle_info_compact); blau/hellgrau je nach top_bar_compact |

Alle in **top_frame**, **row=0**; Layout: `grid(row=0, column=N, ...)`. Im Kompakt-Modus: col 3,5,6 (sep, sep2, minimal_btn) per grid_remove ausgeblendet; Switch-Texte "Language"/"Smooth" per configure(text="") ausgeblendet, DE/EN (col 2) bleibt.

---

## 6. Frames und refs (fuer Callbacks)

- **top_frame:** Immer sichtbar; enthaelt Animation, Switches, Label, Separatoren, Minimal-Button, Info-Button.
- **button_frame:** Nur aufgeklappt; Start, Stop, Keyboard-Button; Ein-/Ausblenden ueber `pack` / `pack_forget`.
- **bottom_frame:** Nur aufgeklappt; Smoothing, API, Keys, Quit; gleiche Ein-/Ausblend-Logik.

Refs fuer Kompakt-Toggle: `sep`, `sep2`, `minimal_btn`, `info_btn` (zusaetzlich zu lang_label, window).

Callbacks in `speech_to_text.py` bekommen `refs` und koennen z.B.:
- `refs["lang_label"].configure(text="DE")` / `"EN"`
- `refs["keyboard_button"].configure(text="Keyboard: On"|"Off")`
- `refs["button_frame"].pack(...)` / `pack_forget()` fuer Minimal-Toggle
- `toggle_info_compact`: lang_switch/transform_switch text="" bzw. LABEL_SPRACHE/LABEL_GLAETTEN; grid_remove/grid fuer sep, sep2, minimal_btn; geometry Breite; info_btn fg_color

---

## 7. Wiedereinstieg auf Experten-Level

- **Layout aendern:** Nur Top-Leiste -> Spalten in `window.py` (grid column 0..7) und diese Sektion 5.
- **Neues Widget in Top-Leiste:** Spalte waehlen, grid(row=0, column=N), ggf. sep verschieben; ASCII in Abschnitt 3/4 anpassen.
- **Zugeklappt vs. Aufgeklappt:** Abschnitt 1 + 2; Code: `height`, `button_frame.pack`/`pack_forget`, `bottom_frame.pack`/`pack_forget`.
- **Kompakt-Modus (i-Button):** Abschnitt 2b + 3b; State `top_bar_compact`; Callback `toggle_info_compact`; Breite WINDOW_WIDTH_COMPACT, refs sep/sep2/minimal_btn/info_btn.
- **Labels/Sprache/Smooth:** `ui/constants.py` (LABEL_SPRACHE, LABEL_GLAETTEN, WINDOW_WIDTH, WINDOW_WIDTH_COMPACT, INFO_BTN_COLOR, INFO_BTN_COLOR_ACTIVE), Switch-Variablen und lang_label ueber refs.

Damit ist die Positionierung und die Verbindung zum Code eindeutig dokumentiert; man kann jederzeit mit "siehe docs/design" auf diesem Stand weiterarbeiten.
