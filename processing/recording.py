# =============================================================================
# PROCESSING/RECORDING.PY – Audio-Aufnahme (ohne UI, ohne Tastatur)
# =============================================================================
# Nur sounddevice + numpy/wave. Stopp erfolgt ueber threading.Event von aussen.
# Aufrufer (speech_to_text.process_recording) startet/stoppt die Animation.
# =============================================================================

import io
import time
import wave
import numpy as np
import sounddevice as sd


def get_available_microphones():
    """
    Gibt Liste aller Eingabegerate zurueck: [{"index": int, "name": str}, ...].
    Index = device_index fuer sounddevice.InputStream(device=...). Duplikate nach Name ausgefiltert.
    """
    try:
        devices = sd.query_devices()
        mics = []
        seen = set()
        for i, device in enumerate(devices):
            if device["max_input_channels"] > 0:
                name = device["name"]
                if name not in seen:
                    mics.append({"index": i, "name": name})
                    seen.add(name)
        return mics
    except Exception as e:
        print(f"Fehler beim Abrufen der Mikrofone: {e}")
        return [{"index": 0, "name": "Standard-Mikrofon"}]


def record_audio(device_index, stop_event, sample_rate=44100):
    """
    Blockierende Aufnahme: liest Chunks (1 Sekunde) bis stop_event.is_set().
    Aufruf aus Daemon-Thread; Main-Thread setzt stop_event bei Strg+Y / Stop-Button.
    device_index: sounddevice device index (z.B. state["selected_mic_index"]).
    Returns: np.ndarray dtype int16, mono; oder leeres Array wenn keine Chunks.
    """
    recording = []
    stream = sd.InputStream(
        samplerate=sample_rate,
        channels=1,
        dtype="int16",
        device=device_index,
    )
    stream.start()
    time.sleep(0.3)
    try:
        while not stop_event.is_set():
            chunk = stream.read(sample_rate)[0]
            recording.append(chunk)
    finally:
        stream.stop()
    if recording:
        return np.concatenate(recording)
    return np.array([], dtype=np.int16)


def audio_to_wav(audio_data, sample_rate=44100):
    """
    Konvertiert np.ndarray (int16, mono) in WAV-Format im Speicher.
    Returns: io.BytesIO, Position 0, bereit fuer .read() (z.B. fuer OpenAI API).
    """
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data.tobytes())
    buf.seek(0)
    return buf
