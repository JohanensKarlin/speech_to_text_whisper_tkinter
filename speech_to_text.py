import sounddevice as sd
import numpy as np
import io
import wave
import pyperclip
import keyboard
import time
import pyautogui
import threading
import customtkinter as ctk
from openai import OpenAI
import json
import os

# API-Schlüssel aus dem JSON-Datei laden
config_file = os.path.join(os.path.dirname(__file__), 'config.json')
with open(config_file, 'r') as f:
    config = json.load(f)
api_key = config['api_key']

# Tastenkombinationen als Variablen
START_RECORDING_KEY = "ctrl+y"  # Geändert von ctrl+a zu ctrl+y
STOP_RECORDING_KEY = "ctrl+y"   # Geändert von ctrl+q zu ctrl+y
TOGGLE_LANGUAGE_KEY = "alt+l"
TOGGLE_KEYBOARD_KEY = "alt+m"
QUIT_APP_KEY = "alt+q"

# OpenAI Client initialisieren (ersetze mit deinem API-Schlüssel)
client = OpenAI(api_key=api_key)

# Globale Variablen für die GUI
status_window = None
status_label = None
animation_frame = None
animation_labels = []
is_recording = False
keyboard_enabled = True  # Neue Variable für Keyboard-Shortcuts
current_language = "de"  # Standardsprache: Deutsch
animation_running = False
animation_id = None
animation_canvas = None

def create_status_window():
    """Erstellt ein schwebendes Statusfenster."""
    global status_window, status_label, animation_frame, animation_labels, keyboard_enabled, animation_canvas
    
    # Farbschema
    bg_color = "#424242"  # Dunkelgrau
    text_color = "white"
    button_bg = "#1E88E5"  # Blau für Buttons
    button_bg_muted = "#666666"  # Dunkleres Grau für Mute-Button, wenn aktiviert
    
    # CustomTkinter Appearance Mode und Default Color Theme setzen
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    # Fenster erstellen
    status_window = ctk.CTk()
    status_window.title("Spracherkennung")
    status_window.geometry("200x120")  # Etwas breiter für 7 Balken
    status_window.attributes("-topmost", True)  # Fenster bleibt immer im Vordergrund
    status_window.overrideredirect(True)  # Entfernt die Titelleiste
    
    # Position in der Mitte des Bildschirms
    screen_width = status_window.winfo_screenwidth()
    screen_height = status_window.winfo_screenheight()
    x_position = (screen_width - 200) // 2
    y_position = (screen_height - 120) // 2
    status_window.geometry(f"200x120+{x_position}+{y_position}")
    
    # Hauptframe mit transparentem Hintergrund
    main_frame = ctk.CTkFrame(status_window, corner_radius=15, fg_color="#333333", border_width=0)
    main_frame.pack(fill="both", expand=True, padx=0, pady=0)
    
    # Content-Frame innerhalb des Hauptframes
    content_frame = ctk.CTkFrame(main_frame, corner_radius=12, fg_color="#333333", border_width=0)
    content_frame.pack(fill="both", expand=True, padx=5, pady=5)
    
    # Oberer Frame für Animation und Sprache
    top_frame = ctk.CTkFrame(content_frame, corner_radius=0, fg_color="transparent")
    top_frame.pack(pady=2)
    
    # Animation Frame (links im top_frame)
    animation_frame = ctk.CTkFrame(top_frame, corner_radius=0, fg_color="transparent")
    animation_frame.grid(row=0, column=0, padx=2)
    
    # Erstelle 7 Labels für die Animation mit absteigender Größe
    animation_labels = []
    # Höhen für die 7 Balken (mittig am höchsten, nach außen absteigend)
    heights = [12, 16, 20, 24, 20, 16, 12]
    
    # Verwende Canvas für präzise Positionierung
    global animation_canvas
    canvas_width = 100
    animation_canvas = ctk.CTkCanvas(animation_frame, width=canvas_width, height=24, 
                                    bg="#333333", highlightthickness=0)
    animation_canvas.pack()
    
    # Berechne die Gesamtbreite aller Balken und Abstände
    bar_width = 6
    bar_spacing = 6
    total_bars_width = (len(heights) * bar_width) + ((len(heights) - 1) * bar_spacing)
    
    # Berechne den Startpunkt, um die Balken zu zentrieren
    start_x = (canvas_width - total_bars_width) / 2
    
    # Erstelle die Balken auf dem Canvas
    for i in range(7):
        # Berechne Position für jeden Balken
        x_pos = start_x + i * (bar_width + bar_spacing)
        height = heights[i]
        y_pos = 24 - height  # Positioniere alle Balken mit der Basis bei y=24
        
        # Erstelle Rechteck für den Balken
        bar = animation_canvas.create_rectangle(
            x_pos, y_pos, x_pos + bar_width, 24,  # x1, y1, x2, y2
            fill="#555555", outline=""
        )
        animation_labels.append(bar)
    
    # Sprach-Toggle Switch (rechts im top_frame)
    lang_switch_var = ctk.StringVar(value="DE")
    lang_switch = ctk.CTkSwitch(
        top_frame,
        text="",
        command=toggle_language,
        variable=lang_switch_var,
        onvalue="DE",
        offvalue="EN",
        width=40,
        height=20,
        switch_width=36,
        switch_height=18,
        corner_radius=10,
        progress_color="#1E88E5"  # Blau
    )
    lang_switch.grid(row=0, column=1, padx=5)
    
    # Label für den Sprachstatus
    lang_label = ctk.CTkLabel(
        top_frame,
        text="DE",
        font=("Arial", 10, "bold"),
        text_color="#FFFFFF"
    )
    lang_label.grid(row=0, column=2, padx=2)
    
    # Button-Frame für Start und Stop
    button_frame = ctk.CTkFrame(content_frame, corner_radius=0, fg_color="transparent")
    button_frame.pack(pady=2)
    
    # Button-Größe für alle Buttons gleich
    button_width = 85
    button_height = 28
    
    # Start-Button
    record_button = ctk.CTkButton(
        button_frame, 
        text="Start", 
        command=start_recording_thread,
        corner_radius=10,
        height=button_height,
        width=button_width,
        fg_color=button_bg,
        hover_color="#1976D2"  # Dunkleres Blau beim Hover
    )
    record_button.grid(row=0, column=0, padx=2)
    
    # Stop-Button
    stop_button = ctk.CTkButton(
        button_frame, 
        text="Stop", 
        command=stop_recording,
        corner_radius=10,
        height=button_height,
        width=button_width,
        fg_color=button_bg,
        hover_color="#1976D2"  # Dunkleres Blau beim Hover
    )
    stop_button.grid(row=0, column=1, padx=2)
    
    # Unterer Frame für Mute und Beenden
    bottom_frame = ctk.CTkFrame(content_frame, corner_radius=0, fg_color="transparent")
    bottom_frame.pack(pady=2)
    
    # Mute-Button mit korrekter Farbe je nach Status
    mute_button = ctk.CTkButton(
        bottom_frame, 
        text="Mute", 
        command=toggle_keyboard,
        corner_radius=10,
        height=button_height,
        width=button_width,
        fg_color=button_bg_muted if not keyboard_enabled else button_bg,
        hover_color="#1976D2"  # Dunkleres Blau beim Hover
    )
    mute_button.grid(row=0, column=0, padx=2)
    
    # Beenden-Button
    quit_button = ctk.CTkButton(
        bottom_frame, 
        text="Beenden", 
        command=quit_app,
        corner_radius=10,
        height=button_height,
        width=button_width,
        fg_color=button_bg,
        hover_color="#1976D2"  # Dunkleres Blau beim Hover
    )
    quit_button.grid(row=0, column=1, padx=2)
    
    # Drag-Funktionalität hinzufügen
    add_drag_functionality(status_window)
    
    # Keyboard-Shortcuts
    status_window.bind(f"<{START_RECORDING_KEY.replace('ctrl', 'Control').replace('+', '-')}>", lambda event: start_recording_thread())
    status_window.bind(f"<{STOP_RECORDING_KEY.replace('ctrl', 'Control').replace('+', '-')}>", lambda event: stop_recording())
    status_window.bind(f"<{TOGGLE_LANGUAGE_KEY.replace('alt', 'Alt').replace('+', '-')}>", lambda event: toggle_language())
    status_window.bind(f"<{TOGGLE_KEYBOARD_KEY.replace('alt', 'Alt').replace('+', '-')}>", lambda event: toggle_keyboard())
    status_window.bind(f"<{QUIT_APP_KEY.replace('alt', 'Alt').replace('+', '-')}>", lambda event: quit_app())
    
    # Fokus auf das Fenster setzen und nach vorne bringen
    status_window.focus_force()
    status_window.lift()
    status_window.update()
    
    return status_window

def update_status(message, color="#424242"):
    """Aktualisiert den Status im Fenster."""
    # Funktion bleibt erhalten, aber macht nichts mehr, da status_label entfernt wurde
    pass

def start_wave_animation():
    """Startet die Wellenanimation für die Aufnahme."""
    global animation_running, animation_id
    
    if not animation_running:
        animation_running = True
        run_wave_animation(0)

def stop_wave_animation():
    """Stoppt die Wellenanimation."""
    global animation_running, animation_id, animation_labels, status_window
    
    animation_running = False
    if animation_id is not None:
        status_window.after_cancel(animation_id)
        animation_id = None
    
    # Setze alle Labels zurück
    for label in animation_labels:
        animation_canvas.itemconfig(label, fill="#555555")

def run_wave_animation(step):
    """Führt einen Schritt der Wellenanimation aus."""
    global animation_labels, animation_running, animation_id, status_window
    
    if not animation_running:
        return
    
    # Farben für die Animation (von dunkel nach hell)
    colors = ["#555555", "#777777", "#999999", "#BBBBBB", "#DDDDDD", "#FFFFFF"]
    
    # Anzahl der Labels
    num_labels = len(animation_labels)
    
    # Animation von links nach rechts
    for i in range(num_labels):
        # Position in der Animation basierend auf dem Schritt
        pos = (step + i) % len(colors)
        # Aktiviere die Farbe für das aktuelle Label
        animation_canvas.itemconfig(animation_labels[i], fill=colors[pos])
    
    # Nächsten Schritt planen
    animation_id = status_window.after(150, run_wave_animation, (step + 1) % len(colors))

def run_reverse_animation(step):
    """Führt einen Schritt der Rückwärts-Animation aus."""
    global animation_labels, animation_running, animation_id, status_window
    
    if not animation_running:
        return
    
    # Farben für die Animation (von dunkel nach hell)
    colors = ["#555555", "#777777", "#999999", "#BBBBBB", "#DDDDDD", "#FFFFFF"]
    
    # Anzahl der Labels
    num_labels = len(animation_labels)
    
    # Animation von rechts nach links
    for i in range(num_labels):
        # Position in der Animation basierend auf dem Schritt (umgekehrte Richtung)
        pos = (step + (num_labels - 1 - i)) % len(colors)
        # Aktiviere die Farbe für das aktuelle Label
        animation_canvas.itemconfig(animation_labels[i], fill=colors[pos])
    
    # Nächsten Schritt planen
    animation_id = status_window.after(150, run_reverse_animation, (step + 1) % len(colors))

def record_audio(fs=44100):
    """Nimmt Audio auf, bis 's' gedrückt wird."""
    global is_recording
    
    # Starte die Aufnahme
    is_recording = True
    start_wave_animation()  # Starte die Animation
    
    print("Aufnahme läuft... Drücke 'Strg+Y' zum Stoppen.")
    recording = []
    stream = sd.InputStream(samplerate=fs, channels=1, dtype='int16')
    stream.start()
    
    # Kleine Verzögerung, um doppelte Tastendrücke zu vermeiden
    time.sleep(0.3)
    
    try:
        while is_recording:
            # Prüfe, ob Strg+Y gedrückt wurde, um die Aufnahme zu stoppen
            if keyboard.is_pressed('ctrl+y'):
                break
                
            chunk = stream.read(fs)[0]  # 1 Sekunde Audio
            recording.append(chunk)
    finally:
        stream.stop()
        is_recording = False
        stop_wave_animation()  # Stoppe die Animation
        print("Aufnahme gestoppt.")
    
    # Prüfe, ob Audiodaten aufgenommen wurden
    if len(recording) > 0:
        start_reverse_animation()  # Starte die Rückwärts-Animation für Transkription
        return np.concatenate(recording)
    else:
        print("Keine Audiodaten aufgenommen.")
        return np.array([])  # Leeres Array zurückgeben

def start_reverse_animation():
    """Startet die Rückwärts-Animation für die Transkription."""
    global animation_running, animation_id
    
    if not animation_running:
        animation_running = True
        run_reverse_animation(0)

def audio_to_wav(audio_data, fs=44100):
    """Konvertiert Audio in WAV-Format im Speicher."""
    wav_file = io.BytesIO()
    with wave.open(wav_file, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(fs)
        wf.writeframes(audio_data.tobytes())
    wav_file.seek(0)
    return wav_file

def transcribe_audio(audio_file):
    """Sendet Audio an die OpenAI API und fügt die Transkription ein."""
    global current_language, animation_running, animation_id
    
    try:
        # Starte die Rückwärts-Animation
        start_reverse_animation()
        
        # Erstelle ein temporäres File-Objekt mit Namen und Dateiendung für die OpenAI API
        from openai.types.audio import Transcription
        import tempfile
        
        # Speichere die Audiodaten in einer temporären Datei
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(audio_file.read())
            temp_path = temp_file.name
        
        # Öffne die temporäre Datei für die API
        with open(temp_path, "rb") as audio:
            # Transkription mit OpenAI
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio,
                language=current_language
            )
        
        # Lösche die temporäre Datei
        import os
        os.unlink(temp_path)
        
        # Stoppe die Animation
        stop_wave_animation()
        
        # Füge den transkribierten Text ein
        pyperclip.copy(transcript.text)
        pyautogui.hotkey('ctrl', 'v')
        
        print(f"Transkription abgeschlossen: {transcript.text}")
        return transcript.text
    except Exception as e:
        print(f"Fehler bei der Transkription: {e}")
        # Stoppe die Animation im Fehlerfall
        stop_wave_animation()
        return None

def start_recording_thread():
    """Startet die Aufnahme in einem separaten Thread."""
    global is_recording
    if not is_recording:
        threading.Thread(target=process_recording).start()

def process_recording():
    """Prozess für Aufnahme und Transkription."""
    audio_data = record_audio()
    if audio_data.size > 0:
        wav_file = audio_to_wav(audio_data)
        transcribe_audio(wav_file)
    else:
        print("Keine Aufnahme erkannt.")
        stop_wave_animation()  # Stelle sicher, dass die Animation gestoppt wird

def stop_recording():
    """Stoppt die Aufnahme."""
    global is_recording
    is_recording = False

def toggle_language():
    """Wechselt zwischen Deutsch und Englisch."""
    global current_language, status_window
    
    if current_language == "de":
        current_language = "en"
        lang_text = "EN"
    else:
        current_language = "de"
        lang_text = "DE"
    
    # Finde das Sprach-Label und aktualisiere den Text
    for widget in status_window.winfo_children():
        if isinstance(widget, ctk.CTkFrame):
            for child in widget.winfo_children():
                if isinstance(child, ctk.CTkFrame):
                    for grandchild in child.winfo_children():
                        if isinstance(grandchild, ctk.CTkFrame):
                            for item in grandchild.winfo_children():
                                if isinstance(item, ctk.CTkLabel) and item.cget("text") in ["DE", "EN"]:
                                    item.configure(text=lang_text)
                                    return

def toggle_keyboard():
    """Schaltet die Keyboard-Shortcuts ein/aus."""
    global keyboard_enabled, status_window
    
    keyboard_enabled = not keyboard_enabled
    
    # Farbschema
    button_bg = "#1E88E5"  # Blau für Buttons
    button_bg_muted = "#666666"  # Dunkleres Grau für Mute-Button, wenn aktiviert
    
    # Finde den Mute-Button und aktualisiere die Farbe
    for widget in status_window.winfo_children():
        if isinstance(widget, ctk.CTkFrame):
            for child in widget.winfo_children():
                if isinstance(child, ctk.CTkFrame):
                    for grandchild in child.winfo_children():
                        if isinstance(grandchild, ctk.CTkFrame):
                            for item in grandchild.winfo_children():
                                if isinstance(item, ctk.CTkButton) and item.cget("text") == "Mute":
                                    if keyboard_enabled:
                                        item.configure(fg_color=button_bg)  # Standard-Farbe
                                    else:
                                        item.configure(fg_color=button_bg_muted)  # Dunklere Farbe
                                    return

def quit_app():
    """Beendet die Anwendung."""
    global status_window
    if status_window:
        status_window.destroy()

def check_keyboard_input():
    """Überprüft Tastatureingaben im Hintergrund."""
    global is_recording, status_window, keyboard_enabled
    
    if keyboard_enabled:
        # Verwende eine Verzögerung zwischen den Tastenprüfungen
        if keyboard.is_pressed(START_RECORDING_KEY) and not is_recording:
            start_recording_thread()
            # Kleine Verzögerung, um doppelte Tastendrücke zu vermeiden
            time.sleep(0.3)
        elif keyboard.is_pressed(STOP_RECORDING_KEY) and is_recording:
            stop_recording()
            # Kleine Verzögerung, um doppelte Tastendrücke zu vermeiden
            time.sleep(0.3)
        elif keyboard.is_pressed(TOGGLE_LANGUAGE_KEY):
            toggle_language()
            time.sleep(0.3)
        elif keyboard.is_pressed(TOGGLE_KEYBOARD_KEY):
            toggle_keyboard()
            time.sleep(0.3)
        elif keyboard.is_pressed(QUIT_APP_KEY):  # Nur Alt+Q beendet die App
            if status_window:
                status_window.destroy()
            return False
    return True

def add_drag_functionality(window):
    """Ermöglicht das Ziehen des Fensters mit der Maus."""
    def start_drag(event):
        # Speichere die initiale Position des Mauszeigers relativ zum Fenster
        window._drag_data = {"x": event.x, "y": event.y}
        
    def on_drag(event):
        # Berechne die neue Position
        if hasattr(window, "_drag_data"):
            # Berechne die Verschiebung
            delta_x = event.x - window._drag_data["x"]
            delta_y = event.y - window._drag_data["y"]
            
            # Bestimme die neue Position
            new_x = window.winfo_x() + delta_x
            new_y = window.winfo_y() + delta_y
            
            # Setze die neue Position
            window.geometry(f"+{new_x}+{new_y}")
    
    def stop_drag(event):
        # Lösche die Drag-Daten
        if hasattr(window, "_drag_data"):
            del window._drag_data
    
    # Binde die Ereignisse an das gesamte Fenster
    window.bind("<ButtonPress-1>", start_drag)
    window.bind("<B1-Motion>", on_drag)
    window.bind("<ButtonRelease-1>", stop_drag)

def main():
    """Hauptfunktion."""
    global status_window
    
    # GUI erstellen
    status_window = create_status_window()
    
    print("Drücke 'Strg+Y' zum Starten und Beenden der Aufnahme, 'Alt+Q' zum Beenden.")
    
    # Hauptschleife für die GUI
    def check_input():
        if check_keyboard_input():
            status_window.after(100, check_input)
        else:
            status_window.quit()
    
    check_input()
    status_window.mainloop()

if __name__ == "__main__":
    main()