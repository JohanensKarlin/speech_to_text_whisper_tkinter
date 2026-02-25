# ui/ – Fenster und Animation

Damit du schnell weisst: Wo die Oberflaeche gebaut wird, wie Callbacks und refs zusammenspielen, und wo du Layout/Animation aenderst.

---

## Zweck

- **Fenster:** Ein schwebendes CustomTkinter-Fenster (immer im Vordergrund, ohne Titelleiste) mit Leiste oben und optional Buttons unten.
- **Animation:** Wellen-Balken auf einem Canvas; Start/Stop und Richtung (Aufnahme vs. Transkription) werden von aussen gesteuert.
- **Keine App-Logik:** UI erzeugt nur Widgets und ruft bei Aktionen Callbacks auf. State und Geschaeftslogik liegen in `speech_to_text.py`.

---

## Module

### constants.py

- **LABEL_SPRACHE**, **LABEL_GLAETTEN**, **WINDOW_WIDTH** – Einheitliche Labels und Fensterbreite (320px). Werden in window.py und in Tests (Design-Check ohne GUI) genutzt.

### window.py

- **create_status_window(callbacks, hotkeys, initial_state, refs)**  
  - Baut das komplette Fenster: Hauptframe, Content, Top-Leiste (Animation, DE/EN-Switch, Transform-Switch, Minimal-Button), optional Button-Frame (Start, Stop, Mic) und Bottom-Frame (Tastatur, Beenden).  
  - Registriert Tk-Bindings fuer die Hotkeys und verbindet sie mit den passenden Callbacks.  
  - Befuellt `refs` mit: `window`, `lang_label`, `lang_switch_var`, `transform_text_var`, `keyboard_button`, `button_frame`, `bottom_frame`, `content_frame`, `top_frame`.  
  - Return: das CTk-Fenster.

- **Hilfsfunktionen:**  
  - `_tk_bind_key(key_str)` – wandelt z. B. "ctrl+y" in "Control-y" fuer Tk.  
  - `_add_drag(window)` – Fenster per Maus ziehen (ButtonPress, B1-Motion, ButtonRelease).

Callbacks kommen aus `speech_to_text.py`; sie lesen/schreiben `state` und aktualisieren ueber `refs` die Widgets (Labels, Button-Text, Frames ein-/ausblenden).

### animation.py

- **init_animation(window, canvas, bar_ids)**  
  Muss einmal aufgerufen werden (von `window.py` nach dem Erstellen des Canvas und der Balken). Speichert Referenzen fuer `after` und `itemconfig`.

- **start_wave_animation()**  
  Startet die Wellen-Animation (Richtung links-nach-rechts). Wird beim Start der Aufnahme aufgerufen.

- **stop_wave_animation()**  
  Stoppt die Animation, cancelt pending `after`, setzt alle Balken auf Ruhefarbe.

- **start_reverse_animation()**  
  Startet Rueckwaerts-Animation (rechts-nach-links). Wird genutzt, waehrend die Transkription laeuft.

Die Animation laeuft ueber `window.after(150, ...)` in einer Schleife; Farben rotieren durch die Balken. Kein eigener Thread.

---

## Abhaengigkeiten

- **customtkinter** – Fenster und Widgets.
- **Aufrufer:** Nur `speech_to_text.py` (importiert und ruft `create_status_window` sowie die Animations-Funktionen auf).

---

## Wo du ansetzt

- **Neues Widget / neuer Button:** In `create_status_window` das Widget bauen, bei Aktion den passenden Callback aus dem `callbacks`-Dict aufrufen. In `speech_to_text.py` den Callback implementieren und in `callbacks` und ggf. `refs` eintragen.
- **Andere Hotkeys:** In `speech_to_text.py` `HOTKEYS` und die Callback-Zuordnung aendern; in `create_status_window` werden nur die uebergebenen `hotkeys` gebunden.
- **Layout, Farben, Groessen:** Direkt in `window.py` (Frames, pack/grid, Farben, Geometrie).
- **Animation schneller/langsamer oder andere Farben:** In `animation.py` die Intervalle (150 ms) und die `COLORS`-Liste aendern.
