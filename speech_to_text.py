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
is_minimal_mode = True  # Standardmäßig im Minimal-Modus starten
selected_mic_index = 0  # Index des ausgewählten Mikrofons
available_mics = []  # Liste der verfügbaren Mikrofone
transform_text_enabled = False  # Neu: Zustand für Texttransformation
transform_text_var = None # Neu: Variable für den Switch

def create_status_window():
    """Erstellt ein schwebendes Statusfenster."""
    global status_window, status_label, animation_frame, animation_labels, keyboard_enabled, animation_canvas
    global is_minimal_mode, transform_text_var # transform_text_var hinzugefügt
    
    #############################################################
    # SCHRITT 1: GRUNDLEGENDE FENSTER- UND DESIGN-EINSTELLUNGEN #
    #############################################################
    
    # Farbschema
    bg_color = "#424242"  # Dunkelgrau
    text_color = "white"
    button_bg = "#1E88E5"  # Blau für Buttons
    button_bg_muted = "#666666"  # Dunkleres Grau für Mute-Button, wenn aktiviert
    
    # CustomTkinter Appearance Mode und Default Color Theme setzen
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    # Create window
    status_window = ctk.CTk()
    status_window.title("Spracherkennung")
    
    #############################################################
    # SCHRITT 2: FENSTERGRÖSSE UND POSITION KONFIGURIEREN      #
    #############################################################
    
    # Fenstergröße basierend auf Modus (minimal oder normal) festlegen
    if is_minimal_mode:
        # MINIMAL MODE DIMENSIONS
        window_width = 280   # Breite des Fensters in Pixeln (erhöht von 220)
        window_height = 40   # Minimale Höhe für den Minimal-Modus
    else:
        # NORMAL MODE DIMENSIONS
        window_width = 280   # Breite des Fensters in Pixeln (erhöht von 220, optional anpassbar)
        window_height = 120  # Normale Höhe für den Standard-Modus
    
    status_window.geometry(f"{window_width}x{window_height}")  # Format: "BreitexHöhe"
    
    status_window.attributes("-topmost", True)  # Fenster bleibt immer im Vordergrund
    status_window.overrideredirect(True)  # Entfernt die Titelleiste
    
    # Fensterposition - Zentriert das Fenster auf dem Bildschirm
    screen_width = status_window.winfo_screenwidth()
    screen_height = status_window.winfo_screenheight()
    x_position = (screen_width - window_width) // 2
    y_position = (screen_height - window_height) // 2
    status_window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")  # Format: "BreitexHöhe+X+Y"
    
    #############################################################
    # SCHRITT 3: HAUPTRAHMEN UND INHALTSRAHMEN ERSTELLEN       #
    #############################################################
    
    # Main frame
    main_frame = ctk.CTkFrame(status_window, corner_radius=15, fg_color="#333333", border_width=0)
    main_frame.pack(fill="both", expand=True, padx=0, pady=0)
    
    # Content frame
    content_frame = ctk.CTkFrame(main_frame, corner_radius=12, fg_color="#333333", border_width=0)
    content_frame.pack(fill="both", expand=True, padx=5, pady=5)
    
    #############################################################
    # SCHRITT 4: OBERER BEREICH - ANIMATION UND SPRACHSTEUERUNG #
    #############################################################
    
    # TOP SECTION - Animation and language controls
    top_frame = ctk.CTkFrame(content_frame, corner_radius=0, fg_color="transparent")
    top_frame.pack(pady=2)  # Vertikaler Abstand
    
    # Animation frame (linke Seite des top_frame)
    animation_frame = ctk.CTkFrame(top_frame, corner_radius=0, fg_color="transparent")
    animation_frame.grid(row=0, column=0, padx=2)  # Horizontaler Abstand
    
    # ANIMATION SETTINGS - Anpassung der Visualisierungsbalken
    animation_labels = []
    # Höhen für die 7 Balken (höchste in der Mitte, nach außen abnehmend)
    heights = [12, 16, 20, 24, 20, 16, 12]  # Höhe jedes Balkens in Pixeln
    
    # Canvas für präzise Positionierung
    global animation_canvas
    canvas_width = 100  # Breite des Animations-Canvas
    canvas_height = 24  # Höhe des Animations-Canvas
    animation_canvas = ctk.CTkCanvas(animation_frame, width=canvas_width, height=canvas_height, 
                                    bg="#333333", highlightthickness=0)
    animation_canvas.pack()
    
    # ANIMATION BAR SETTINGS
    bar_width = 6       # Breite jedes Balkens in Pixeln
    bar_spacing = 6     # Abstand zwischen den Balken in Pixeln
    total_bars_width = (len(heights) * bar_width) + ((len(heights) - 1) * bar_spacing)
    
    # Startpunkt berechnen, um die Balken zu zentrieren
    start_x = (canvas_width - total_bars_width) / 2
    
    # Balken auf dem Canvas erstellen
    for i in range(7):
        # Position für jeden Balken berechnen
        x_pos = start_x + i * (bar_width + bar_spacing)
        height = heights[i]
        y_pos = canvas_height - height  # Positioniere alle Balken mit Basis bei y=canvas_height
        
        # Rechteck für den Balken erstellen
        bar = animation_canvas.create_rectangle(
            x_pos, y_pos, x_pos + bar_width, canvas_height,  # x1, y1, x2, y2
            fill="#555555", outline=""
        )
        animation_labels.append(bar)
    
    #############################################################
    # SCHRITT 5: SPRACHSCHALTER UND MINIMAL-MODUS-BUTTON       #
    #############################################################
    
    # LANGUAGE TOGGLE SETTINGS
    # Sprachumschalter (rechte Seite des top_frame)
    lang_switch_var = ctk.StringVar(value="DE")
    lang_switch = ctk.CTkSwitch(
        top_frame,
        text="",
        command=toggle_language,
        variable=lang_switch_var,
        onvalue="DE",
        offvalue="EN",
        width=40,          # Breite des Schalters
        height=20,         # Höhe des Schalters
        switch_width=36,   # Breite des Schalter-Sliders
        switch_height=18,  # Höhe des Schalter-Sliders
        corner_radius=10,  # Abgerundete Ecken
        progress_color="#1E88E5"  # Blau
    )
    lang_switch.grid(row=0, column=1, padx=5)  # Horizontaler Abstand
    
    # Sprachstatus-Label
    lang_label = ctk.CTkLabel(
        top_frame,
        text="DE",
        font=("Arial", 10, "bold"),
        text_color="#FFFFFF"
    )
    lang_label.grid(row=0, column=2, padx=2)  # Horizontaler Abstand
    
    # NEU: TRANSFORM TEXT TOGGLE
    global transform_text_var # Sicherstellen, dass es die globale Variable ist
    transform_text_var = ctk.BooleanVar(value=transform_text_enabled)
    transform_switch = ctk.CTkSwitch(
        top_frame,
        text="", # Kein Text direkt am Switch
        variable=transform_text_var,
        command=toggle_transform_text, # Neuer Callback
        onvalue=True,
        offvalue=False,
        width=40,
        height=20,
        switch_width=36,
        switch_height=18,
        corner_radius=10,
        progress_color="#00D100"  # Grün für diesen Schalter
    )
    transform_switch.grid(row=0, column=3, padx=(5,2)) # Nach dem lang_label

    # Tooltip für den neuen Schalter (optional, aber gut für UX)
    # Hier könnte man eine kleine Info-Icon oder Text daneben setzen
    # transform_info_label = ctk.CTkLabel(top_frame, text="T", font=("Arial", 10), text_color="#FFFFFF")
    # transform_info_label.grid(row=0, column=4, padx=(0,5))
    # Tooltip-Logik würde komplexer, daher erstmal ohne für Einfachheit

    # MINIMAL MODE BUTTON - Größe und Position nach Bedarf anpassen
    minimal_button = ctk.CTkButton(
        top_frame, 
        text="⚊",  # Unicode-Symbol für Minimieren
        command=toggle_minimal_mode,
        width=24,           # Breite des Buttons (erhöht von 20 auf 24)
        height=20,          # Höhe des Buttons
        corner_radius=10,   # Abgerundete Ecken
        fg_color=button_bg,
        hover_color="#1976D2",  # Dunkleres Blau beim Hover
        font=("Arial", 10, "bold")
    )
    minimal_button.grid(row=0, column=4, padx=3)  # Geändert von column=3 zu column=4
    
    #############################################################
    # SCHRITT 6: HAUPTBUTTONS - START UND STOP                 #
    #############################################################
    
    # MAIN BUTTONS SECTION - Start and Stop
    button_frame = ctk.CTkFrame(content_frame, corner_radius=0, fg_color="transparent")
    
    # BUTTON DIMENSIONS - Ändern Sie diese Werte, um alle Hauptbuttons anzupassen
    button_width = 65    # Breite der Hauptbuttons (reduziert für 3 Buttons in einer Reihe)
    button_height = 28   # Höhe der Hauptbuttons
    
    # Start button
    record_button = ctk.CTkButton(
        button_frame, 
        text="Start", 
        command=start_recording_thread,
        corner_radius=10,       # Abgerundete Ecken
        height=button_height,   # Button-Höhe
        width=button_width,     # Button-Breite
        fg_color=button_bg,
        hover_color="#1976D2"   # Dunkleres Blau beim Hover
    )
    record_button.grid(row=0, column=0, padx=2)  # Horizontaler Abstand
    
    # Stop button
    stop_button = ctk.CTkButton(
        button_frame, 
        text="Stop", 
        command=stop_recording,
        corner_radius=10,       # Abgerundete Ecken
        height=button_height,   # Button-Höhe
        width=button_width,     # Button-Breite
        fg_color=button_bg,
        hover_color="#1976D2"   # Dunkleres Blau beim Hover
    )
    stop_button.grid(row=0, column=1, padx=2)  # Horizontaler Abstand
    
    # Mic button - NEU
    mic_button = ctk.CTkButton(
        button_frame, 
        text="Mic", 
        command=select_microphone,
        corner_radius=10,       # Abgerundete Ecken
        height=button_height,   # Button-Höhe
        width=button_width,     # Button-Breite
        fg_color=button_bg,
        hover_color="#1976D2"   # Dunkleres Blau beim Hover
    )
    mic_button.grid(row=0, column=2, padx=2)  # Horizontaler Abstand
    
    #############################################################
    # SCHRITT 7: UNTERER BEREICH - TASTATUR-STEUERUNG UND STATUS #
    #############################################################
    
    # BOTTOM SECTION - Keyboard control and status
    bottom_frame = ctk.CTkFrame(content_frame, corner_radius=0, fg_color="transparent")
    
    # Keyboard toggle button
    keyboard_button = ctk.CTkButton(
        bottom_frame, 
        text="Tastatur: An", 
        command=toggle_keyboard,
        corner_radius=10,
        height=24,          # Reduzierte Höhe für den unteren Button
        width=110,          # Breite des Buttons
        fg_color=button_bg,
        hover_color="#1976D2"
    )
    keyboard_button.grid(row=0, column=0, padx=2)
    
    # Quit button
    quit_button = ctk.CTkButton(
        bottom_frame, 
        text="Beenden", 
        command=quit_app,
        corner_radius=10,
        height=24,          # Reduzierte Höhe für den unteren Button
        width=60,           # Reduzierte Breite für den Beenden-Button
        fg_color="#E53935", # Rot für den Beenden-Button
        hover_color="#C62828" # Dunkleres Rot beim Hover
    )
    quit_button.grid(row=0, column=1, padx=2)
    
    #############################################################
    # SCHRITT 8: FENSTER-DRAG-FUNKTIONALITÄT HINZUFÜGEN         #
    #############################################################
    
    # Drag functionality
    add_drag_functionality(status_window)
    
    #############################################################
    # SCHRITT 9: MODUS-ABHÄNGIGE ANZEIGE DER ELEMENTE           #
    #############################################################
    
    # Im Minimal-Modus die Button- und Bottom-Frames ausblenden
    if is_minimal_mode:
        button_frame.pack_forget()  # Button-Frame nicht anzeigen
        bottom_frame.pack_forget()  # Bottom-Frame nicht anzeigen
    else:
        # Im normalen Modus alle Frames anzeigen
        button_frame.pack(pady=2)  # Vertikaler Abstand
        bottom_frame.pack(pady=2)  # Vertikaler Abstand
    
    #############################################################
    # SCHRITT 10: TASTATUR-SHORTCUTS EINRICHTEN                 #
    #############################################################
    
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
    stream = sd.InputStream(samplerate=fs, channels=1, dtype='int16', device=selected_mic_index)
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
        
        # Lade die bekannten Halluzinationstexte
        hallucination_file = os.path.join(os.path.dirname(__file__), 'hallucination.json')
        with open(hallucination_file, 'r', encoding='utf-8') as f:
            hallucinations = json.load(f)
        
        # Filtere Halluzinationen basierend auf der aktuellen Sprache
        original_transcription = transcript.text # Originale Transkription sichern
        filtered_text = original_transcription
        lang_key = current_language
        
        # Fallback auf 'en', wenn die aktuelle Sprache nicht in den Halluzinationen vorhanden ist
        if lang_key not in hallucinations:
            lang_key = 'en'
            
        # Wenn Halluzinationen für die aktuelle Sprache vorhanden sind
        if lang_key in hallucinations:
            # Verwende reguläre Ausdrücke für eine bessere Filterung
            import re
            
            # Erstelle eine Liste aller Halluzinationen für die aktuelle Sprache
            hallucination_patterns = hallucinations[lang_key]
            
            # Verarbeite jede Halluzination
            for pattern in hallucination_patterns:
                # Entferne führende und abschließende Leerzeichen vom Muster
                pattern = pattern.strip()
                
                # Erstelle einen Regex-Pattern, der unabhängig von Groß-/Kleinschreibung ist
                # und auch Teile des Textes findet
                if pattern:
                    # Escape spezielle Regex-Zeichen im Muster
                    escaped_pattern = re.escape(pattern)
                    # Erstelle den Regex mit Flags für Groß-/Kleinschreibung und Multiline
                    regex = re.compile(escaped_pattern, re.IGNORECASE | re.MULTILINE)
                    # Ersetze alle Vorkommen durch leeren String
                    filtered_text = regex.sub('', filtered_text)
            
            # Entferne doppelte Leerzeichen und bereinige den Text
            filtered_text = re.sub(r'\s+', ' ', filtered_text).strip()
            
            # Protokolliere die Filterung für Debugging-Zwecke
            if filtered_text != original_transcription:
                print(f"Halluzination gefiltert: Original: '{original_transcription}' -> Gefiltert: '{filtered_text}'")
        
        # NEU: Texttransformation mit gpt-4o-mini, falls aktiviert
        global transform_text_enabled # Zugriff auf globale Variable
        if transform_text_enabled and filtered_text:
            print("INFO: Texttransformation wird versucht...")
            try:
                transformation_prompt = (
                    "Diese Nachricht wurde automatisch über ein Voice-to-Speech-Tool aufgenommen und soll nun an Projekt-Teilnehmer gehen oder Team-Mitglieder. "
                    "Bitte korrigiere sie nur leicht auf grammatikalische Fehler, damit der Lesefluss besser ist, da die Nachricht mit Sprache aufgenommen worden ist. "
                    "Der Ton soll ähnlich bleiben, so wie an Team-Mitglieder, die sehr gut miteinander umgehen. Kein förmlicher Oberton. "
                    "Gib NUR den korrigierten Text zurück, ohne zusätzliche Erklärungen oder Einleitungen."
                    "Verzichte auf eigene Antworte, wie z.B. gerne ändere ich den Text für dich."
                    "das Sprachtool verwendet zum beispiel keine Zeilenumbrüche nach der Begrüßung, füge diese hinzu"
                )
                
                response = client.chat.completions.create(
                    model="gpt-4o-mini", # Dein gewünschtes Modell
                    messages=[
                        {"role": "system", "content": "Du bist ein hilfreicher Assistent, der Texte basierend auf Spracherkennung leicht korrigiert und den informellen Ton beibehält."},
                        {"role": "user", "content": f"{transformation_prompt}\n\nOriginaltext:\n\"{filtered_text}\""}
                    ],
                    temperature=0.5 # Etwas Kreativität erlauben, aber nicht zu viel
                )
                
                transformed_text = response.choices[0].message.content.strip()
                
                # Manchmal fügen Modelle trotzdem Anführungszeichen am Anfang/Ende hinzu
                if transformed_text.startswith('"') and transformed_text.endswith('"'):
                    transformed_text = transformed_text[1:-1]
                
                print(f"Text transformiert: Original: '{filtered_text}' -> Transformiert: '{transformed_text}'")
                filtered_text = transformed_text # Verwende den transformierten Text
            except Exception as e:
                print(f"Fehler bei der Texttransformation: {e}. Verwende ursprünglichen Text.")
                # Im Fehlerfall wird der bisherige filtered_text (nach Halluzinationsfilter) verwendet

        # Füge den gefilterten transkribierten Text ein
        if filtered_text: # Nur einfügen, wenn Text vorhanden ist
            pyperclip.copy(filtered_text)
            pyautogui.hotkey('ctrl', 'v')
            print(f"Transkription abgeschlossen: {filtered_text}")
        else:
            print("Transkription ergab keinen Text nach Filterung/Transformation.")
        
        return filtered_text
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
    button_bg_muted = "#666666"  # Dunkleres Grau für deaktivierten Button
    
    # Finde den Tastatur-Button und aktualisiere Text und Farbe
    for widget in status_window.winfo_children():
        if isinstance(widget, ctk.CTkFrame):
            for child in widget.winfo_children():
                if isinstance(child, ctk.CTkFrame):
                    for grandchild in child.winfo_children():
                        if isinstance(grandchild, ctk.CTkFrame):
                            for item in grandchild.winfo_children():
                                if isinstance(item, ctk.CTkButton) and ("Tastatur" in item.cget("text")):
                                    # Aktualisiere Text und Farbe basierend auf dem Status
                                    if keyboard_enabled:
                                        item.configure(text="Tastatur: An", fg_color=button_bg)
                                    else:
                                        item.configure(text="Tastatur: Aus", fg_color=button_bg_muted)
                                    return
    
    # Alternative Suche, falls der Button nicht gefunden wurde
    all_widgets = status_window.winfo_children()
    for widget in all_widgets:
        if hasattr(widget, 'winfo_children'):
            for child in widget.winfo_children():
                if hasattr(child, 'winfo_children'):
                    for grandchild in child.winfo_children():
                        if hasattr(grandchild, 'winfo_children'):
                            for item in grandchild.winfo_children():
                                if isinstance(item, ctk.CTkButton) and ("Tastatur" in str(item.cget("text"))):
                                    # Aktualisiere Text und Farbe basierend auf dem Status
                                    if keyboard_enabled:
                                        item.configure(text="Tastatur: An", fg_color=button_bg)
                                    else:
                                        item.configure(text="Tastatur: Aus", fg_color=button_bg_muted)
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

def toggle_minimal_mode():
    """Wechselt zwischen normalem und minimalem Modus."""
    global status_window, is_minimal_mode, animation_frame
    
    # Referenzen auf die Frames im Fenster finden
    all_frames = status_window.winfo_children()
    if not all_frames:
        return
        
    main_frame = all_frames[0]  # Main frame is the first child
    if not main_frame.winfo_children():
        return
        
    content_frame = main_frame.winfo_children()[0]  # Content frame is the first child of main frame
    
    # Alle Frames im Content-Frame finden
    frames_in_content = content_frame.winfo_children()
    
    # Frames identifizieren
    top_frame = None
    button_frame = None
    bottom_frame = None
    
    # Frames nach ihrer Position im Fenster identifizieren
    for frame in frames_in_content:
        if isinstance(frame, ctk.CTkFrame):
            # Verwende den Namen des Frames, wenn er gesetzt wurde
            if hasattr(frame, '_name') and frame._name:
                if 'top' in frame._name.lower():
                    top_frame = frame
                elif 'button' in frame._name.lower():
                    button_frame = frame
                elif 'bottom' in frame._name.lower():
                    bottom_frame = frame
            # Ansonsten nach Position im Fenster identifizieren
            elif frame.winfo_y() < 30:  # Oberer Bereich
                top_frame = frame
            elif frame.winfo_y() < 60:  # Mittlerer Bereich
                button_frame = frame
            else:  # Unterer Bereich
                bottom_frame = frame
    
    # Suche nach den Frames, die möglicherweise nicht angezeigt werden
    if not button_frame or not bottom_frame:
        for widget in content_frame.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                # Prüfe, ob es sich um einen der gesuchten Frames handelt
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkButton):
                        if child.cget("text") == "Start":
                            button_frame = widget
                        elif child.cget("text") == "Beenden":
                            bottom_frame = widget
    
    if is_minimal_mode:
        # Wechsel zum normalen Modus
        if button_frame:
            # Stelle sicher, dass der Button-Frame angezeigt wird
            button_frame.pack(pady=2, after=top_frame)
        if bottom_frame:
            # Stelle sicher, dass der Bottom-Frame angezeigt wird
            bottom_frame.pack(pady=2, after=button_frame)
        
        # NORMAL MODE DIMENSIONS - Ändere diese Werte, um die normale Fenstergröße anzupassen
        window_width = 280    # Normale Fensterbreite
        window_height = 120   # Normale Fensterhöhe
        status_window.geometry(f"{window_width}x{window_height}")
        
        # Zentriere das Fenster erneut
        screen_width = status_window.winfo_screenwidth()
        screen_height = status_window.winfo_screenheight()
        x_position = (screen_width - window_width) // 2
        y_position = (screen_height - window_height) // 2
        status_window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        
        # Aktualisiere das Fenster, um die Änderungen anzuzeigen
        status_window.update()
        
        is_minimal_mode = False
    else:
        # Wechsel zum minimalen Modus
        if button_frame:
            button_frame.pack_forget()
        if bottom_frame:
            bottom_frame.pack_forget()
        
        # MINIMAL MODE DIMENSIONS - Ändere diese Werte, um die minimale Fenstergröße anzupassen
        window_width = 280   # Minimale Fensterbreite
        window_height = 40   # Minimale Fensterhöhe
        status_window.geometry(f"{window_width}x{window_height}")
        
        # Zentriere das Fenster erneut
        screen_width = status_window.winfo_screenwidth()
        screen_height = status_window.winfo_screenheight()
        x_position = (screen_width - window_width) // 2
        y_position = (screen_height - window_height) // 2
        status_window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        
        is_minimal_mode = True

def get_available_microphones():
    """Gibt eine Liste der verfügbaren Mikrofone zurück."""
    try:
        devices = sd.query_devices()
        # Nur Eingabegeräte filtern
        mics = []
        seen_names = set()  # Für Duplikaterkennung
        
        # Sammle alle Eingabegeräte
        for i, device in enumerate(devices):
            # Prüfe, ob es sich um ein Eingabegerät handelt
            if device['max_input_channels'] > 0:
                device_name = device['name']
                # Überspringe Duplikate
                if device_name not in seen_names:
                    mics.append({'index': i, 'name': device_name})
                    seen_names.add(device_name)
        
        return mics
    except Exception as e:
        print(f"Fehler beim Abrufen der Mikrofone: {e}")
        return [{'index': 0, 'name': 'Standard-Mikrofon'}]

def select_microphone():
    """Öffnet ein Dialogfenster zur Auswahl des Mikrofons."""
    global selected_mic_index, available_mics, status_window
    
    if not available_mics:
        available_mics = get_available_microphones()
    
    # Erstelle ein neues Fenster für die Mikrofonauswahl
    mic_window = ctk.CTkToplevel(status_window)
    mic_window.title("Mikrofon auswählen")
    mic_window.geometry("300x250")
    mic_window.attributes("-topmost", True)
    
    # Zentriere das Fenster
    screen_width = mic_window.winfo_screenwidth()
    screen_height = mic_window.winfo_screenheight()
    x_position = (screen_width - 300) // 2
    y_position = (screen_height - 250) // 2
    mic_window.geometry(f"300x250+{x_position}+{y_position}")
    
    # Überschrift
    ctk.CTkLabel(
        mic_window, 
        text="Verfügbare Mikrofone:", 
        font=("Arial", 14, "bold")
    ).pack(pady=(15, 5))
    
    # Frame für die Mikrofonliste
    list_frame = ctk.CTkFrame(mic_window, fg_color="transparent")
    list_frame.pack(fill="both", expand=True, padx=10, pady=5)
    
    # Scrollbare Liste für Mikrofone
    scrollable_frame = ctk.CTkScrollableFrame(list_frame, width=280, height=150)
    scrollable_frame.pack(fill="both", expand=True)
    
    # Radiobutton-Variable
    selected_var = ctk.IntVar(value=selected_mic_index)
    
    # Füge Radiobuttons für jedes Mikrofon hinzu
    for mic in available_mics:
        radio = ctk.CTkRadioButton(
            scrollable_frame,
            text=mic['name'],
            value=mic['index'],
            variable=selected_var,
            font=("Arial", 12)
        )
        radio.pack(anchor="w", pady=2, padx=5)
    
    # OK-Button
    def on_ok():
        global selected_mic_index
        selected_mic_index = selected_var.get()
        mic_window.destroy()
    
    ctk.CTkButton(
        mic_window,
        text="OK",
        command=on_ok,
        width=100,
        height=30,
        corner_radius=10,
        fg_color="#1E88E5",
        hover_color="#1976D2"
    ).pack(pady=15)

def toggle_transform_text():
    """Callback für den Texttransformations-Schalter."""
    global transform_text_enabled, transform_text_var
    transform_text_enabled = transform_text_var.get()
    if transform_text_enabled:
        print("Text-Transformation AKTIVIERT") # Für Debugging
        # Hier könnte man z.B. das Icon des Schalters ändern oder ein Label aktualisieren
    else:
        print("Text-Transformation DEAKTIVIERT") # Für Debugging

def main():
    """Hauptfunktion."""
    global status_window, available_mics
    
    # Verfügbare Mikrofone abrufen
    available_mics = get_available_microphones()
    
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