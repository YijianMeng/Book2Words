import tkinter as tk
from tkinter import messagebox, ttk
import os, re, sqlite3
from PIL import Image
import pytesseract, jieba
from wordfreq import top_n_list
import spacy
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from DanishDictionary_module import translate_danish_word

# --- Folders ---
BOOKS_DIR = os.path.join(os.getcwd(), "book")
WORDS_DIR = os.path.join(os.getcwd(), "word")
os.makedirs(WORDS_DIR, exist_ok=True)

DB_PATH = os.path.join(WORDS_DIR, "lightsql.db")

# --- Language Resources ---
nlp_da = spacy.load("da_core_news_sm")
english_words = set(top_n_list("en", 30000))
danish_words = set(top_n_list("da", 30000))


# --- PDF Export Function ---
def export_word_definitions_to_pdf(db_path, output_pdf, table_name):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(
            f'''
            SELECT word, definition, page_number, book_name
            FROM {table_name}
            ORDER BY page_number ASC, word ASC
            '''
        )
        rows = cursor.fetchall()
    except sqlite3.OperationalError:
        messagebox.showwarning("No Data", f"No table found for {table_name}")
        conn.close()
        return
    conn.close()

    if not rows:
        messagebox.showwarning("No Data", f"No word definitions found in {table_name}")
        return

    # ✅ Remove duplicates (keep only first occurrence)
    seen = set()
    unique_rows = []
    for word, definition, page_number, book_name in rows:
        if word not in seen:
            unique_rows.append((word, definition, page_number, book_name))
            seen.add(word)

    # Prepare PDF data
    data = [["Word", "Definition", "Page Number", "Book Name"]] + unique_rows
    pdf = SimpleDocTemplate(output_pdf, pagesize=letter)
    table = Table(data, colWidths=[100, 200, 80, 150])

    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ])
    table.setStyle(style)
    pdf.build([table])

    messagebox.showinfo("PDF Exported", f"PDF saved to {output_pdf}")


# --- Translator App ---
class TranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Book Translator & PDF")

        # Select book
        tk.Label(root, text="Select Book:").pack()
        self.book_var = tk.StringVar()
        self.book_options = self.get_books()
        if self.book_options:
            self.book_var.set(self.book_options[0])
        self.book_menu = tk.OptionMenu(root, self.book_var, *self.book_options)
        self.book_menu.pack()

        # PDF name entry
        tk.Label(root, text="PDF Name:").pack()
        self.pdf_entry = tk.Entry(root)
        self.pdf_entry.pack()
        if self.book_options:
            self.pdf_entry.insert(0, f"{self.book_options[0]}_definitions.pdf")

        # Update filename when book changes
        self.book_var.trace_add("write", self.update_pdf_name)

        # Progress bar
        self.progress = ttk.Progressbar(root, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", padx=10, pady=5)

        # Action button
        tk.Button(root, text="Translate & Create PDF", command=self.translate_and_pdf).pack(pady=10)

    def get_books(self):
        return sorted([f for f in os.listdir(BOOKS_DIR) if os.path.isdir(os.path.join(BOOKS_DIR, f))])

    def update_pdf_name(self, *args):
        book_name = self.book_var.get().strip()
        if book_name:
            self.pdf_entry.delete(0, tk.END)
            self.pdf_entry.insert(0, f"{book_name}_definitions.pdf")

    def translate_and_pdf(self):
        book_name = self.book_var.get()
        folder_path = os.path.join(BOOKS_DIR, book_name)
        if not os.path.exists(folder_path):
            messagebox.showerror("Error", "Book folder missing")
            return

        pdf_name = self.pdf_entry.get().strip()
        if not pdf_name.endswith(".pdf"):
            pdf_name += ".pdf"
        pdf_path = os.path.join(WORDS_DIR, pdf_name)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Each book gets its own table
        table_name = f"word_definitions_{book_name}"
        cursor.execute(f'''CREATE TABLE IF NOT EXISTS {table_name}
                        (word TEXT, definition TEXT, page_number INTEGER, book_name TEXT)''')

        # Collect image files
        image_files = [f for f in sorted(os.listdir(folder_path)) if f.lower().endswith((".jpg", ".png",".jpeg"))]
        self.progress["maximum"] = len(image_files)
        self.progress["value"] = 0

        for filename in image_files:
            page_number = int(re.findall(r'\d+', filename)[-1])
            img_path = os.path.join(folder_path, filename)
            img = Image.open(img_path)

            # Detect rotation
            try:
                osd = pytesseract.image_to_osd(img)
                rotation_angle = int([l for l in osd.split("\n") if "Rotate:" in l][0].split(":")[1].strip())
            except:
                rotation_angle = 0
            if rotation_angle != 0:
                img = img.rotate(-rotation_angle, expand=True)

            # OCR
            ocr_data = pytesseract.image_to_data(img, lang="eng+dan", config="--oem 3 --psm 6",
                                                 output_type=pytesseract.Output.DICT)
            all_words = []
            for w in ocr_data['text']:
                w = re.sub(r"[^\w\u4e00-\u9fff]", "", w)
                if w.strip() != "":
                    all_words.append(w)

            filtered_words = [w for w in all_words if len(w) > 2]
            doc = nlp_da(" ".join(filtered_words))
            lemmas_set = set([token.lemma_ for token in doc])

            # Language detection
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

            # Collect words
            word_list = []
            for word in all_words:
                if majority_lang == "en" and word.lower() in english_words:
                    word_list.append(word)
                elif majority_lang == "da" and word.lower() in danish_words:
                    word_list.append(word)
                elif majority_lang == "zh":
                    word_list.extend(jieba.lcut(word))

            # Translate Danish
            top_freq_danish = set(top_n_list("da", 500))
            for word_i in word_list:
                doc_i = nlp_da(word_i)
                lemma_i = doc_i[0].lemma_ if doc_i else word_i.lower()
                is_danish = lemma_i in danish_words and len(word_i) > 2
                if is_danish and lemma_i not in top_freq_danish:
                    word_def = translate_danish_word(word_i, speedy=True)
                    if word_def:
                        word, definition = word_i, word_def[1]
                        cursor.execute(
                            f'SELECT 1 FROM {table_name} WHERE word=? AND book_name=? AND page_number=?',
                            (word, book_name, page_number))
                        if cursor.fetchone() is None:
                            cursor.execute(
                                f'INSERT INTO {table_name}(word, definition, page_number, book_name) VALUES(?,?,?,?)',
                                (word, definition, page_number, book_name))

            # Update progress bar
            self.progress["value"] += 1
            self.root.update_idletasks()

        conn.commit()
        conn.close()

        export_word_definitions_to_pdf(DB_PATH, pdf_path, table_name)


# --- Run App ---
if __name__ == "__main__":
    root = tk.Tk()
    app = TranslatorApp(root)
    root.mainloop()
