from PIL import Image
import pytesseract
import jieba
from wordfreq import top_n_list
import re
from collections import Counter
import spacy
from DanishDictionary_module import translate_danish_word, get_danish_lexicon
nlp_da = spacy.load("da_core_news_sm")  # pip install da_core_news_sm
import sqlite3

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

# Connect to your lightsql database
conn = sqlite3.connect('lightsql.db')
cursor = conn.cursor()

# Create table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS word_definitions (
        word TEXT,
        definition TEXT,
        page_number INTEGER,
        book_name TEXT
    )
''')

def export_word_definitions_to_pdf(
    db_path='lightsql.db',
    output_pdf='word_definitions.pdf',
    table_name='word_definitions'
):
    """Exports the word definitions table to a PDF file."""
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Fetch data from the table
        cursor.execute(f'''
            SELECT word, definition, page_number, book_name FROM {table_name}
        ''')
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            print("⚠️ No data found in the table.")
            return

        # Add a header row
        data = [['Word', 'Definition', 'Page Number', 'Book Name']] + rows

        # Create PDF document
        pdf = SimpleDocTemplate(output_pdf, pagesize=letter)
        table = Table(data, colWidths=[100, 200, 80, 150])

        # Define table style
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ])
        table.setStyle(style)

        # Build PDF
        pdf.build([table])
        print(f"✅ PDF successfully exported to: {output_pdf}")

    except Exception as e:
        print(f"❌ Error during PDF export: {e}")


def is_danish_word(word: str):
    """
    Check if a Danish word exists in the dictionary.
    Returns a tuple: (is_valid: bool, lemma: str)
    """
    doc = nlp_da(word.lower())
    lemma = doc[0].lemma_ if doc else word.lower()
    is_valid = lemma in danish_words and len(word) > 2
    return is_valid, lemma

def majority_detection(lemmas_set):
    lang_votes = {"en": 0, "da": 0, "zh": 0}
    for w in lemmas_set:
        lw = w.lower()
        if lw in english_words:
            print(lw)
            lang_votes["en"] += 1
        elif lw in danish_words:
            lang_votes["da"] += 1
        elif re.search(r"[\u4e00-\u9fff]", w):
            lang_votes["zh"] += 1

    majority_lang = max(lang_votes, key=lang_votes.get)

    print(f"Detected majority language: {majority_lang}\n")
    return majority_lang

# --- Step 0: Load word lists using wordfreq ---
english_words = set(top_n_list("en", 30000))
danish_words = set(top_n_list("da", 30000))
danish_words_list=list(danish_words)
# --- Step 1: Open image ---
page_number=1
book_name="skammerens_datter"
img = Image.open("skammerens_datter/skammerens_datter_72.jpg")

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
    lang="eng+dan",
    config="--oem 3 --psm 6",#"--oem 3 --psm 6",
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

# filter longer words
filtered_words_for_vote = [w for w in all_words if len(w) > 2]
nlp = spacy.load("da_core_news_sm")
doc = nlp(" ".join(filtered_words_for_vote))
#doc = nlp(filtered_words_for_vote)
lemmas = [token.lemma_ for token in doc]  # ["gå", "gå", "gå"]
lemmas_set=set(lemmas)

majority_lang=majority_detection(lemmas_set)
word_list = []

for word in all_words:
    if majority_lang == "en":
        if word.lower() in english_words and len(word) > 2:
            word_list.append(word)
    elif majority_lang == "da":
        if word.lower() in danish_words and len(word) > 2:
            word_list.append(word)
    elif majority_lang == "zh":
        # Use jieba to split Chinese text
        word_list.extend(jieba.lcut(word))
    else:
        continue  # fallback: skip unknown languages


top_freq_danish = set(top_n_list("da", 500))
NO_freq_word=True
for word_i in list(word_list):
    IsDanish,lemma_i=is_danish_word(word_i)
    #lemma = doc[0].lemma_.lower()
    if IsDanish:
        should_translate = (
            (NO_freq_word and lemma_i not in top_freq_danish) or
            (not NO_freq_word)
        )

        if should_translate:
            word_def = translate_danish_word(word_i, speedy=True)
            if word_def:
                word, definition = word_i, word_def[1]
                print(f"{word}: {word_def}")

                # Save to database
                cursor.execute('''
                    SELECT 1 FROM word_definitions
                    WHERE word = ? AND book_name = ? AND page_number = ?
                ''', (word, book_name, page_number))

                if cursor.fetchone() is None:
                    # Insert only if not already in database
                    cursor.execute('''
                        INSERT INTO word_definitions (word, definition, page_number, book_name)
                        VALUES (?, ?, ?, ?)
                    ''', (word, definition, page_number, book_name))
conn.commit()
conn.close()




conn = sqlite3.connect('lightsql.db')
cursor = conn.cursor()

cursor.execute('SELECT * FROM word_definitions')
rows = cursor.fetchall()



# Print results
print("📖 Contents of 'word_definitions':")
for row in rows:
    print(row)

# Close connection
conn.close()

export_word_definitions_to_pdf()
