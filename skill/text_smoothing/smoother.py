# =============================================================================
# SKILL/TEXT_SMOOTHING/SMOOTHER.PY – GPT-Nachbearbeitung (Text glätten)
# =============================================================================
# Wird von processing.transcription aufgerufen wenn transform_enabled=True.
# Nutzt prompts.get_prompts(language) fuer System- und User-Prompt. Kein UI.
# =============================================================================

from .prompts import get_prompts


def smooth_transcription(
    client,
    text: str,
    language: str,
    model: str = "gpt-4o-mini",
    custom_system: str | None = None,
    custom_user: str | None = None,
):
    """
    Sendet Rohtext an Chat-Completions. Wenn custom_system und custom_user gesetzt,
    werden diese verwendet; sonst get_prompts(language). Entfernt Anfuehrungszeichen
    am Rand. Bei Fehler: Originaltext zurueck.
    """
    if not text or not text.strip():
        return text

    if custom_system and custom_user:
        system_content = custom_system
        user_instruction = custom_user
    else:
        prompts = get_prompts(language)
        system_content = prompts["system"]
        user_instruction = prompts["user"]

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": f"{user_instruction}\n\nOriginaltext:\n\"{text}\""},
            ],
            temperature=0.5,
        )
        transformed = response.choices[0].message.content.strip()
        if transformed.startswith('"') and transformed.endswith('"'):
            transformed = transformed[1:-1]
        return transformed
    except Exception as e:
        print(f"Fehler bei der Texttransformation: {e}. Verwende urspruenglichen Text.")
        return text
