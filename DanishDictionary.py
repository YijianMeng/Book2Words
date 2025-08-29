import requests
from googletrans import Translator
import wn


wn.add("dannet-wn-lmf.xml.gz")


# Example word
word = "hund"  # Danish for "dog"

# Retrieve synsets for the word
synsets = wn.synsets(word, lang='da')
translator = Translator()

# Display definitions
#for synset in synsets:
#    print(f"Definition: {synset.definition()}")
for s in synsets:
    da_def = s.definition()
    en_def = translator.translate(da_def, src='da', dest='en').text
    #print(f"Danish: {da_def}")
    print(f"English: {en_def}")





# --- Step 1: Get Danish definition from Wiktionary ---
def get_danish_definition(word):
    url = "https://da.wiktionary.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "titles": word,
        "prop": "extracts",
        "exintro": True,
        "explaintext": True
    }
    headers = {
        "User-Agent": "Camera2Dict/1.0 (your_email@example.com)"  # Replace with your email
    }

    response = requests.get(url, params=params, headers=headers)
    if response.status_code != 200:
        return None

    try:
        data = response.json()
    except requests.exceptions.JSONDecodeError:
        return None

    page = next(iter(data['query']['pages'].values()))
    definition = page.get('extract', '').strip()
    return definition if definition else None

# --- Step 2: Translate Danish definition or fallback word to English ---
def get_danish_lexion(word):
    translator = Translator()
    synsets = wn.synsets(word, lang='da')  # 'da' is not accepted, use 'dan'

    english_translations = []

    for i_num, s in enumerate(synsets):
        da_def = s.definition()
        en_def = translator.translate(da_def, src='da', dest='en').text
        english_translations.append(f"{i_num}, {en_def} ;")

    return "\n".join(english_translations)

def translate_danish_word(word):
    danish_def = get_danish_definition(word)
    danish_lexion = get_danish_lexion(word)
    print(danish_lexion)

    if danish_lexion:
        print(danish_lexion)

    if danish_def:
        english_def = translator.translate(danish_def, src='da', dest='en').text
        return danish_def, english_def
    else:
        # Fallback: translate the word itself
        english_translation = translator.translate(word, src='da', dest='en').text
        return None, english_translation

# --- Step 3: Example usage ---
words = ['går', 'jeg', 'der', 'Normalt']

for w in words:
    da_def, en_def = translate_danish_word(w)
    print(f"Word: {w}")
    print(f"  Danish definition: {da_def}")
    print(f"  English translation: {en_def}")
    print()


# Example word
word = "hund"  # Danish for "dog"

# Retrieve synsets for the word


