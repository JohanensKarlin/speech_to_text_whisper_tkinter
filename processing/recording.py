# =============================================================================
# PROCESSING/RECORDING.PY – Audio-Aufnahme (ohne UI, ohne Tastatur)
# =============================================================================
# Nur sounddevice + numpy/wave. Stopp erfolgt ueber threading.Event von aussen.
# Aufrufer (speech_to_text.process_recording) startet/stoppt die Animation.
# =============================================================================

import io
import subprocess
import sys
import time
import wave
from collections.abc import Mapping
import numpy as np
import sounddevice as sd


def _hostapi_name_map():
    try:
        hosts = sd.query_hostapis()
    except Exception:
        return {}
    out = {}
    for i, host in enumerate(hosts):
        if isinstance(host, Mapping):
            out[i] = str(host.get("name", ""))
    return out


def _hostapi_priority(name):
    n = (name or "").lower()
    if "wasapi" in n:
        return 0
    if "wdm-ks" in n:
        return 1
    if "directsound" in n:
        return 2
    if "mme" in n:
        return 3
    if "asio" in n:
        return 4
    return 9


def _normalized_device_key(name):
    base = (name or "").strip().lower()
    if "hands-free" in base:
        return ""
    aliases = [
        "microphone array",
        "mikrofonarray",
        "microphone",
        "mikrofon",
        "headset microphone",
        "kopfh\u00f6rer",
        "kopfh\ufffd\u00f6rer",
        "kopfh",
    ]
    for p in aliases:
        if base.startswith(p):
            l = base.find("(")
            r = base.rfind(")")
            if 0 <= l < r:
                return base[l + 1 : r].strip()
    return base


def _looks_like_real_input(name):
    n = (name or "").lower()
    bad = [
        "soundmapper",
        "prim\u00e4rer soundaufnahmetreiber",
        "primarer soundaufnahmetreiber",
        "primary sound capture driver",
        "input ()",
        "loopback",
        "output",
        "lautsprecher",
    ]
    return not any(token in n for token in bad)


def _windows_active_capture_keys():
    if sys.platform != "win32":
        return set()
    cmd = (
        "$caps = Get-PnpDevice -Class AudioEndpoint | "
        "Where-Object { $_.Status -eq 'OK' -and $_.InstanceId -match '{0\\.0\\.1\\.' }; "
        "$caps | Select-Object -ExpandProperty FriendlyName"
    )
    try:
        out = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", cmd],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=4,
        )
    except Exception:
        return set()
    keys = set()
    for line in out.splitlines():
        name = line.strip()
        if name:
            keys.add(_normalized_device_key(name))
    return keys


def _can_open_input(device_index, sample_rate, channels):
    ch = max(1, int(channels or 1))
    sr = int(sample_rate or 44100)
    try:
        sd.check_input_settings(device=device_index, samplerate=sr, channels=ch)
        return True
    except Exception:
        return False


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
            if not isinstance(device, Mapping):
                continue
            if int(device.get("max_input_channels", 0) or 0) > 0:
                name = str(device.get("name", f"Mic {i}"))
                if name not in seen:
                    mics.append({"index": i, "name": name})
                    seen.add(name)
        return mics
    except Exception as e:
        print(f"Fehler beim Abrufen der Mikrofone: {e}")
        return [{"index": 0, "name": "Standard-Mikrofon"}]


def get_active_microphones():
    """
    Liefert moeglichst nur benutzbare Input-Geraete.
    Ergebnis: [{'index': int, 'name': str, 'channels': int, 'samplerate': int}, ...]
    """
    try:
        devices = sd.query_devices()
    except Exception as e:
        print(f"Fehler beim Abrufen aktiver Mikrofone: {e}")
        return []

    host_names = _hostapi_name_map()
    default_hostapi = None
    try:
        default_devices = sd.default.device
        default_input_idx = None
        if isinstance(default_devices, (list, tuple)) and len(default_devices) > 0:
            if default_devices[0] is not None:
                default_input_idx = int(default_devices[0])
        elif default_devices is not None:
            default_input_idx = int(default_devices)
        if default_input_idx is not None and 0 <= default_input_idx < len(devices):
            dflt = next(
                (
                    d
                    for j, d in enumerate(devices)
                    if j == default_input_idx and isinstance(d, Mapping)
                ),
                None,
            )
            if isinstance(dflt, Mapping):
                default_hostapi = int(dflt.get("hostapi", -1) or -1)
    except Exception:
        default_hostapi = None
    active_capture_keys = _windows_active_capture_keys()
    candidates = []

    raw_candidates = []
    for i, dev in enumerate(devices):
        if not isinstance(dev, Mapping):
            continue
        try:
            max_in = int(dev.get("max_input_channels", 0) or 0)
            if max_in <= 0:
                continue
            name = str(dev.get("name", f"Mic {i}"))
            if not _looks_like_real_input(name):
                continue
            norm_key = _normalized_device_key(name)
            if not norm_key:
                continue
            if active_capture_keys and norm_key not in active_capture_keys:
                continue
            host_idx = int(dev.get("hostapi", -1) or -1)
            host_name = host_names.get(host_idx, "")
            sr = int(dev.get("default_samplerate", 44100) or 44100)
            ch = min(max_in, 1)
            if not _can_open_input(i, sr, ch):
                continue
            raw_candidates.append(
                {
                    "index": i,
                    "name": name,
                    "channels": max_in,
                    "samplerate": max(8000, sr),
                    "hostapi_index": host_idx,
                    "hostapi": host_name,
                    "key": norm_key,
                }
            )
        except Exception:
            continue

    if default_hostapi is not None:
        preferred = [
            m for m in raw_candidates if m.get("hostapi_index") == default_hostapi
        ]
        candidates = preferred if preferred else raw_candidates
    else:
        candidates = raw_candidates

    if not candidates:
        return []

    best_by_key = {}
    for mic in candidates:
        key = mic["key"]
        rank = _hostapi_priority(mic.get("hostapi", ""))
        existing = best_by_key.get(key)
        if existing is None:
            best_by_key[key] = mic
            continue
        ex_rank = _hostapi_priority(existing.get("hostapi", ""))
        if rank < ex_rank:
            best_by_key[key] = mic

    out = []
    for mic in best_by_key.values():
        out.append(
            {
                "index": int(mic["index"]),
                "name": str(mic["name"]),
                "channels": int(mic["channels"]),
                "samplerate": int(mic["samplerate"]),
            }
        )
    out.sort(key=lambda m: m["name"].lower())
    return out


def compute_audio_level(chunk):
    """RMS-Level in [0..1] fuer Visualisierung."""
    if chunk is None or getattr(chunk, "size", 0) == 0:
        return 0.0
    mono = np.asarray(chunk, dtype=np.float32).reshape(-1)
    rms = float(np.sqrt(np.mean(np.square(mono))) / 32768.0)
    return max(0.0, min(1.0, rms * 3.0))


def record_audio(
    device_index,
    stop_event,
    sample_rate=44100,
    gain=1.0,
    level_callback=None,
    retry_attempts=2,
    return_sample_rate=False,
):
    """
    Blockierende Aufnahme: liest Chunks (1 Sekunde) bis stop_event.is_set().
    Aufruf aus Daemon-Thread; Main-Thread setzt stop_event bei Strg+Y / Stop-Button.
    device_index: sounddevice device index (z.B. state["selected_mic_index"]).
    Returns: np.ndarray dtype int16, mono; oder leeres Array wenn keine Chunks.
    Wenn return_sample_rate=True: (audio_data, used_sample_rate).
    """
    last_error = None
    preferred_rates = []
    if sample_rate:
        preferred_rates.append(int(sample_rate))
    for sr in (48000, 44100, 32000, 24000, 16000, 8000):
        if sr not in preferred_rates:
            preferred_rates.append(sr)

    for attempt in range(retry_attempts + 1):
        recording = []
        stream = None
        try:
            opened = False
            used_sr = int(preferred_rates[0])
            last_open_error = None
            for sr in preferred_rates:
                try:
                    stream = sd.InputStream(
                        samplerate=sr,
                        channels=1,
                        dtype="int16",
                        device=device_index,
                        blocksize=max(1024, int(sr / 8)),
                    )
                    stream.start()
                    opened = True
                    used_sr = int(sr)
                    break
                except Exception as open_err:
                    last_open_error = open_err
                    stream = None
            if not opened:
                raise RuntimeError(
                    f"Kein gueltiger Sample-Rate gefunden: {last_open_error}"
                )
            if stream is None:
                raise RuntimeError("Audio-Stream konnte nicht geoeffnet werden")
            time.sleep(0.2)
            while not stop_event.is_set():
                chunk = stream.read(max(1024, int(used_sr / 8)))[0]
                if gain != 1.0:
                    amplified = np.clip(
                        chunk.astype(np.float32) * float(gain),
                        -32768,
                        32767,
                    ).astype(np.int16)
                    chunk = amplified
                if level_callback:
                    try:
                        level_callback(compute_audio_level(chunk))
                    except Exception:
                        pass
                recording.append(chunk)
            if recording:
                audio_data = np.concatenate(recording)
            else:
                audio_data = np.array([], dtype=np.int16)
            if return_sample_rate:
                return audio_data, used_sr
            return audio_data
        except Exception as e:
            last_error = e
            if attempt < retry_attempts:
                time.sleep(0.25)
                continue
            raise RuntimeError(f"Audioaufnahme fehlgeschlagen: {e}") from e
        finally:
            if stream is not None:
                try:
                    stream.stop()
                except Exception:
                    pass
                try:
                    stream.close()
                except Exception:
                    pass
            if level_callback:
                try:
                    level_callback(0.0)
                except Exception:
                    pass
    raise RuntimeError(f"Audioaufnahme fehlgeschlagen: {last_error}")


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
