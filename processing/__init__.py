# processing – Aufnahme (record_audio, audio_to_wav, get_available_microphones) und
# Transkription (transcribe: Whisper + Halluzinationsfilter + optional skill text_smoothing).
from .recording import (
    record_audio,
    audio_to_wav,
    get_available_microphones,
    get_active_microphones,
    compute_audio_level,
)
from .transcription import transcribe

__all__ = [
    "record_audio",
    "audio_to_wav",
    "get_available_microphones",
    "get_active_microphones",
    "compute_audio_level",
    "transcribe",
]
