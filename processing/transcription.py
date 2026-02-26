# =============================================================================
# PROCESSING/TRANSCRIPTION.PY – Whisper + Nachbearbeitung
# =============================================================================
# Ablauf: WAV in Temp-Datei -> OpenAI audio.transcriptions -> Halluzinationsfilter
# (hallucination.json pro Sprache) -> optional skill/text_smoothing (GPT, sprachabhaengig).
# Kein UI, nur client + Pfade + Flags. Aufrufer steuert Animation.
# =============================================================================

import json
import os
import re
import sys
import tempfile

from skill.text_smoothing import smooth_transcription


def _load_hallucinations(hallucination_path):
    """Laedt hallucination.json: Dict mit Sprachen als Keys, Listen von Mustern als Values."""
    if hasattr(sys, '_MEIPASS'):
        hallucination_path = os.path.join(sys._MEIPASS, "hallucination.json")
    with open(hallucination_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _filter_hallucinations(text, lang_key, hallucinations):
    """
    Entfernt bekannte Halluzinations-Phrasen (z.B. Untertitel-Hinweise) per Regex.
    lang_key: "de", "en", etc. Fallback auf "en" wenn Sprache nicht in JSON.
    """
    if lang_key not in hallucinations:
        lang_key = "en"
    if lang_key not in hallucinations:
        return text
    filtered = text
    for pattern in hallucinations[lang_key]:
        pattern = pattern.strip()
        if not pattern:
            continue
        escaped = re.escape(pattern)
        regex = re.compile(escaped, re.IGNORECASE | re.MULTILINE)
        filtered = regex.sub("", filtered)
    return re.sub(r"\s+", " ", filtered).strip()


def transcribe(
    client,
    audio_file,
    language,
    hallucination_path,
    transform_enabled,
    model_transcribe="gpt-4o-mini-transcribe",
    custom_smoother_system=None,
    custom_smoother_user=None,
    smoother_model=None,
):
    """
    Pipeline: WAV -> Whisper API -> Halluzinationsfilter -> optional smooth_transcription (Skill).
    custom_smoother_system/user: wenn beide gesetzt, werden sie an smooth_transcription uebergeben (Custom-Prompts).
    Returns: fertiger Text oder None bei Exception.
    """
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_file.read())
            tmp_path = tmp.name
        try:
            with open(tmp_path, "rb") as audio:
                transcript = client.audio.transcriptions.create(
                    model=model_transcribe,
                    file=audio,
                    language=language,
                )
        finally:
            os.unlink(tmp_path)

        raw_text = transcript.text
        hallucinations = _load_hallucinations(hallucination_path)
        filtered_text = _filter_hallucinations(raw_text, language, hallucinations)
        if filtered_text != raw_text:
            print(f"Halluzination gefiltert: '{raw_text}' -> '{filtered_text}'")

        if transform_enabled and filtered_text:
            filtered_text = smooth_transcription(
                client,
                filtered_text,
                language,
                custom_system=custom_smoother_system,
                custom_user=custom_smoother_user,
                model=smoother_model or "gpt-4o-mini",
            )

        return filtered_text or None
    except Exception as e:
        print(f"Fehler bei der Transkription: {e}")
        return None
