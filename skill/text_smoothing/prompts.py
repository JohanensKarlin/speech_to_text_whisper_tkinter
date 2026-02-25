# =============================================================================
# SKILL/TEXT_SMOOTHING/PROMPTS.PY – Sprachabhaengige Prompts fuer Text-Glaettung
# =============================================================================
# Nach der Spracherkennung kann der Rohtext per GPT leicht korrigiert werden
# (Grammatik, Lesefluss, Zeilenumbrueche). Sprache (de/en) waehlt den Prompt.
# Erweiterung: weitere Sprachen als Keys in PROMPTS hinzufuegen.
# =============================================================================

PROMPTS = {
    "de": {
        "system": (
            "Du bist ein hilfreicher Assistent, der Texte basierend auf Spracherkennung "
            "leicht korrigiert und den informellen Ton beibehält."
        ),
        "user": (
            "Diese Nachricht wurde automatisch über ein Voice-to-Speech-Tool aufgenommen und soll nun an "
            "Projekt-Teilnehmer gehen oder Team-Mitglieder. "
            "Bitte korrigiere sie nur leicht auf grammatikalische Fehler, damit der Lesefluss besser ist, "
            "da die Nachricht mit Sprache aufgenommen worden ist. "
            "Der Ton soll ähnlich bleiben, so wie an Team-Mitglieder, die sehr gut miteinander umgehen. "
            "Kein förmlicher Oberton. "
            "Gib NUR den korrigierten Text zurück, ohne zusätzliche Erklärungen oder Einleitungen. "
            "Verzichte auf eigene Antworte, wie z.B. gerne ändere ich den Text für dich. "
            "Das Sprachtool verwendet zum Beispiel keine Zeilenumbrüche nach der Begrüßung, füge diese hinzu."
        ),
    },
    "en": {
        "system": (
            "You are a helpful assistant that lightly corrects speech-to-text transcriptions "
            "and keeps the informal tone."
        ),
        "user": (
            "This message was recorded automatically via a voice-to-text tool and will be sent to "
            "project participants or team members. "
            "Please correct it only lightly for grammar so the flow is better, "
            "since the message was captured by speech. "
            "Keep the tone similar, as for team members who work well together. No formal tone. "
            "Return ONLY the corrected text, without explanations or introductions. "
            "Do not add your own replies like 'I'll be happy to change that for you'. "
            "The speech tool does not add line breaks after greetings; add them where appropriate."
        ),
    },
}


def get_prompts(lang: str) -> dict:
    """Liefert {"system": str, "user": str} fuer die Sprache. Unbekannte Sprache -> DE."""
    return PROMPTS.get(lang, PROMPTS["de"])
