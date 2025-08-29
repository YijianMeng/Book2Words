import requests
from googletrans import Translator
import wn

# Load WordNet resource (make sure you have the file locally)
wn.add("dannet-wn-lmf.xml.gz")

translator = Translator()


# --- Wiktionary lookup ---
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
    headers = {
        "User-Agent": "Camera2Dict/1.0 (your_email@example.com)"  # replace email
    }

    response = requests.get(url, params=params, headers=headers)
    if response.status_code != 200:
        return None

    try:
        data = response.json()
    except requests.exceptions.JSONDecodeError:
        return None

    page = next(iter(data["query"]["pages"].values()))
    definition = page.get("extract", "").strip()
    return definition if definition else None


# --- WordNet lookup ---
def get_danish_lexicon(word: str) -> list[str]:
    """Retrieve English translations of Danish WordNet definitions."""
    synsets = wn.synsets(word, lang="da")  # "da" works for Danish

    translations = []
    for i_num, s in enumerate(synsets):
        da_def = s.definition()
        en_def = translator.translate(da_def, src="da", dest="en").text
        translations.append(f"{i_num}: {en_def}")
    return translations


# --- Combined translation ---
def translate_danish_word(word: str) -> tuple[str | None, str]:
    """
    Translate a Danish word:
      - Try Wiktionary definition (Danish + English).
      - If unavailable, fall back to direct word translation.
    """
    danish_def = get_danish_definition(word)
    lexicon = get_danish_lexicon(word)
    if lexicon:
        return None,lexicon
    if danish_def:
        english_def = translator.translate(danish_def, src="da", dest="en").text
        return danish_def, english_def
    else:
        english_translation = translator.translate(word, src="da", dest="en").text
        return None, english_translation


# --- Example usage (only runs when executed directly) ---
if __name__ == "__main__":
    words = ["går", "jeg", "hund", "Normalt"]

    for w in words:
        da_def, en_def = translate_danish_word(w)
        print(f"Word: {w}")
        print(f"  Danish definition: {da_def}")
        print(f"  English translation: {en_def}")

        lex = get_danish_lexicon(w)
        if lex:
            print("  Lexicon entries:")
            for l in lex:
                print("   -", l)
        print()

    # Example single word
    word = "hund"
    print("Lexicon for 'hund':", get_danish_lexicon(word))
