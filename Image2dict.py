import tkinter as tk
from tkinter import messagebox
import cv2
import os
from PIL import Image, ImageTk
import sqlite3
from datetime import datetime


DB_NAME = "vocab.db"

# ------------------- Database -------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vocab (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT UNIQUE,
            definition TEXT,
            book TEXT,
            page INTEGER,
            learned INTEGER DEFAULT 0,
            times_remembered INTEGER DEFAULT 0,
            last_checked TEXT,
            sentence TEXT
        )
    """)
    conn.commit()
    conn.close()


def add_word(word, definition, book, page, sentence):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM vocab WHERE word = ?", (word,))
    if cursor.fetchone():
        conn.close()
        return False  # already exists

    cursor.execute("""
        INSERT INTO vocab (word, definition, book, page, sentence, last_checked)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (word, definition, book, page, sentence, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return True


# ------------------- GUI -------------------
class BookScannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Book Page Scanner")

        # Book name
        tk.Label(root, text="Book Name:").grid(row=0, column=0, padx=5, pady=5)
        self.book_entry = tk.Entry(root)
        self.book_entry.grid(row=0, column=1, padx=5, pady=5)

        # Page number
        tk.Label(root, text="Page Number:").grid(row=1, column=0, padx=5, pady=5)
        self.page_entry = tk.Entry(root)
        self.page_entry.grid(row=1, column=1, padx=5, pady=5)
        self.page_entry.insert(0, "1")

        # Live preview
        self.video_label = tk.Label(root)
        self.video_label.grid(row=2, column=0, columnspan=2, pady=5)

        # Capture button
        tk.Button(root, text="Capture Page", command=self.capture_page).grid(
            row=3, column=0, columnspan=2, pady=10
        )

        # Start camera
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Could not open camera")
            self.root.destroy()
            return

        self.update_camera()

    def update_camera(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)
        self.root.after(10, self.update_camera)

    def capture_page(self):
        book_name = self.book_entry.get().strip()
        page_number = self.page_entry.get().strip()

        if not book_name or not page_number.isdigit():
            messagebox.showerror("Error", "Enter valid book name and page number")
            return

        folder = os.path.join(os.getcwd(), book_name)
        os.makedirs(folder, exist_ok=True)

        filename = f"{book_name}_{page_number}.jpg"
        filepath = os.path.join(folder, filename)

        ret, frame = self.cap.read()
        if ret:
            cv2.imwrite(filepath, frame)
            messagebox.showinfo("Saved", f"Saved {filename}")

            # Example: insert dummy word into DB
            # (Later we’ll run OCR and add real words)
            test_word = "hund"
            test_sentence = "Jeg har en hund i huset."
            add_word(test_word, "dog", book_name, int(page_number), test_sentence)

            # Increment page number
            self.page_entry.delete(0, tk.END)
            self.page_entry.insert(0, str(int(page_number) + 1))
        else:
            messagebox.showerror("Error", "Failed to capture image")

    def __del__(self):
        if hasattr(self, "cap") and self.cap.isOpened():
            self.cap.release()


if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    app = BookScannerApp(root)
    root.mainloop()
