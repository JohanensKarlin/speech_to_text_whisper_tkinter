# skill/ – Ausgelagerte Funktionen (Text-Glaettung)

Damit du schnell weisst: Wo die GPT-Text-Glaettung sitzt, wie die Sprache gewaehlt wird, und wo du Prompts oder Modell aenderst.

---

## Zweck

- **text_smoothing:** Nach der Spracherkennung kann der Rohtext per GPT leicht korrigiert werden (Grammatik, Lesefluss, Zeilenumbrueche). Die Sprache (de/en) bestimmt den Prompt; unbekannte Sprachen fallen auf DE zurueck.

Aufrufer ist nur `processing.transcription.transcribe`, wenn `transform_enabled=True`. Kein UI, keine anderen Abhaengigkeiten ausser OpenAI-Client und Text.

---

## text_smoothing/

### prompts.py

- **PROMPTS** – Dict mit Keys `"de"` und `"en"`. Pro Sprache: `"system"` (Rolle) und `"user"` (Anweisung an das Modell).
- **get_prompts(lang)** – Liefert `{"system": ..., "user": ...}` fuer die uebergebene Sprache. Unbekannte Sprache -> Fallback auf `"de"`.

Wenn du Prompts aenderst (z. B. formeller, andere Sprache, andere Anweisung): nur hier aendern. Neue Sprache = neuen Key in `PROMPTS` anlegen und in `get_prompts` keinen Fallback noetig (weiterhin Fallback auf DE).

### smoother.py

- **smooth_transcription(client, text, language, model="gpt-4o-mini")**  
  - Ruft `get_prompts(language)` auf, sendet mit dem erhaltenen System- und User-Prompt eine Chat-Completion (mit dem uebergebenen `client`).  
  - Entfernt am Anfang/Ende des Ergebnisses Anfuehrungszeichen, falls das Modell sie hinzugefuegt hat.  
  - Bei Fehler: gibt den urspruenglichen `text` zurueck und loggt den Fehler.

---

## Datenfluss (fuer dich)

1. `processing.transcription.transcribe` hat nach Whisper und Halluzinationsfilter den Text und `transform_enabled=True`.
2. Es ruft `smooth_transcription(client, filtered_text, language)` auf.
3. `smooth_transcription` holt die Prompts fuer `language`, sendet an die Chat-API, bereinigt die Antwort und gibt sie zurueck.
4. `transcribe` gibt diesen Text als Endergebnis zurueck.

---

## Wo du ansetzt

- **Prompts aendern (Ton, Regeln, Zeilenumbrueche):** `skill/text_smoothing/prompts.py` – `PROMPTS["de"]` / `PROMPTS["en"]` anpassen.
- **Weitere Sprache (z. B. fr):** In `prompts.py` `PROMPTS["fr"]` mit `system` und `user` hinzufuegen. Aufrufer muss dann `language="fr"` uebergeben (bereits ueber `state["current_language"]` moeglich, wenn du in der UI eine dritte Sprache anbietest).
- **Anderes Modell oder Parameter:** In `smoother.py` den Default `model` oder zusaetzliche API-Parameter (z. B. `temperature`) aendern.
