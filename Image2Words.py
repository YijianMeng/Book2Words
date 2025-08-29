from PIL import Image
import pytesseract
import jieba
from wordfreq import top_n_list
import re
from collections import Counter
import spacy
from DanishDictionary_module import translate_danish_word, get_danish_lexicon


# --- Step 0: Load word lists using wordfreq ---
english_words = set(top_n_list("en", 30000))
danish_words = set(top_n_list("da", 30000))
danish_words_list=list(danish_words)
# --- Step 1: Open image ---
img = Image.open("page2.jpeg")

# --- Step 2: Detect rotation ---
try:
    osd = pytesseract.image_to_osd(img)
    rotation_angle = int([l for l in osd.split("\n") if "Rotate:" in l][0].split(":")[1].strip())
except Exception:
    rotation_angle = 0

if rotation_angle != 0:
    img = img.rotate(-rotation_angle, expand=True)

# --- Step 3: OCR with multi-language support ---
ocr_data = pytesseract.image_to_data(
    img,
    lang="dan",
    config="--oem 3 --psm 6",
    output_type=pytesseract.Output.DICT
)

# --- Step 4: Organize words by line ---
lines = {}
all_words = []
for i, word in enumerate(ocr_data['text']):
    word = re.sub(r"[^\w\u4e00-\u9fff]", "", word)  # keep alphanumeric + Chinese
    if word.strip() == "":
        continue

    line_id = (ocr_data['block_num'][i], ocr_data['par_num'][i], ocr_data['line_num'][i])
    if line_id not in lines:
        lines[line_id] = []
    lines[line_id].append(word)
    all_words.append(word)

# --- Step 5: Majority language detection ---
lang_votes = Counter()
filtered_words_for_vote = [w for w in all_words if len(w) > 2]

nlp = spacy.load("da_core_news_sm")
doc = nlp(" ".join(filtered_words_for_vote))

#doc = nlp(filtered_words_for_vote)
lemmas = [token.lemma_ for token in doc]  # ["gå", "gå", "gå"]
lemmas_set=set(lemmas)


lang_votes = {"en": 0, "da": 0, "zh": 0}

for w in lemmas_set:
    lw = w.lower()
    if lw in english_words:
        lang_votes["en"] += 1
    elif lw in danish_words:
        lang_votes["da"] += 1
    elif re.search(r"[\u4e00-\u9fff]", w):
        lang_votes["zh"] += 1

majority_lang = max(lang_votes, key=lang_votes.get)

#majority_lang = lang_votes.most_common(1)[0][0] if lang_votes else "unknown"
#majority_lang="da"
print(f"Detected majority language: {majority_lang}\n")

# --- Step 6: Filter words using majority language ---
final_lines = {}
word_list = []

for line_id, words in lines.items():
    if majority_lang == "en":
        filtered_words = [w for w in words if w.lower() in english_words]
        print(filtered_words)
    elif majority_lang == "da":
        filtered_words = [w for w in words if w.lower() in danish_words]
    elif majority_lang == "zh":
        filtered_words = list(jieba.lcut("".join(words)))
    else:
        filtered_words = words  # fallback
    word_list.extend(filtered_words)
    final_lines[line_id] = (majority_lang, filtered_words)

# --- Step 7: Print results ---
print(f"Detected rotation: {rotation_angle}°\n")
for line_id in sorted(final_lines.keys()):
    lang, words = final_lines[line_id]
    print(f"Line {line_id} [{lang}]: {' '.join(words)}")

#nltk.download('wordnet')


# Example word
#word = "ran"

# # Get synsets (sets of synonyms with meanings)
# synsets = wn.synsets(word)
#
# print(f"Definitions for '{word}':")
# for syn in synsets:
#     print(f"- {syn.definition()}")  # word definition
#     print(f"  Examples: {syn.examples()}")  # example sentences
#     print(f"  Synonyms: {syn.lemma_names()}")
#     print(f"  Hypernyms (more general): {[h.name() for h in syn.hypernyms()]}")
#     print(f"  Hyponyms (more specific): {[h.name() for h in syn.hyponyms()]}")
#     print()
