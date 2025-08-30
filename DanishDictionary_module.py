import requests
from deep_translator import GoogleTranslator
import wn
from functools import lru_cache

# --- Setup ---
# Load WordNet resource only when needed
WN_LOADED = False

# Initialize GoogleTranslator globally
translator = GoogleTranslator(source='da', target='en')

# Reuse a single session for Wiktionary requests
session = requests.Session()
session.headers.update({"User-Agent": "Camera2Dict/1.0 (your_email@example.com)"})


# --- Wiktionary lookup ---
@lru_cache(maxsize=256)
def get_danish_definition(word: str) -> str | None:
    """Fetch Danish definition of a word from Wiktionary (if available)."""
    url = "https://da.wiktionary.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "titles": word,
        "prop": "extracts",
        "exintro": True,
        "explaintext": True,
    }

    try:
        response = session.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
    except Exception:
        return None

    page = next(iter(data.get("query", {}).get("pages", {}).values()), {})
    definition = page.get("extract", "").strip()
    return definition if definition else None


# --- WordNet lookup ---
@lru_cache(maxsize=256)
def get_danish_lexicon(word: str) -> list[str]:
    """Retrieve English translations of Danish WordNet definitions."""
    global WN_LOADED
    if not WN_LOADED:
        wn.add("dannet-wn-lmf.xml.gz")
        WN_LOADED = True

    synsets = wn.synsets(word, lang="da")

    translations = []
    for i_num, s in enumerate(synsets):
        da_def = s.definition()
        try:
            en_def = translator.translate(da_def)
        except Exception as e:
            en_def = f"[Translation error: {e}]"
        translations.append(f"{i_num}: {en_def}")
    return translations


# --- Combined translation ---
def translate_danish_word(word: str, speedy: bool = False) -> tuple[str | None, str | list[str]]:
    """
    Translate a Danish word:
      - Try WordNet lexicon if speedy=False
      - Else try Wiktionary definition
      - Else fall back to direct word translation
    """
    if not speedy:
        lexicon = get_danish_lexicon(word)
        if lexicon:
            return None, lexicon

    danish_def = get_danish_definition(word)
    if danish_def:
        try:
            english_def = translator.translate(danish_def)
        except Exception as e:
            english_def = f"[Translation error: {e}]"
        return danish_def, english_def

    try:
        english_translation = translator.translate(word)
    except Exception as e:
        english_translation = f"[Translation error: {e}]"
    return None, english_translation


# --- Example usage ---
if __name__ == "__main__":
    words = ["går", "jeg", "hund", "Normalt"]

    for w in words:
        da_def, en_def = translate_danish_word(w, speedy=True)
        print(f"Word: {w}")
        print(f"  Danish definition: {da_def}")
        print(f"  English: {en_def}")

    # Example single word
    word = "hund"
    print("Lexicon for 'hund':", get_danish_lexicon(word))
