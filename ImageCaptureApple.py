import tkinter as tk
from tkinter import messagebox
import cv2
import os
from PIL import Image, ImageTk
import threading
import shutil  # needed for deleting folders

# Language codes for folder naming
language_codes = {
    "English": "eng",
    "Danish": "dan",
    "Chinese": "chi"
}

BOOKS_DIR = os.path.join(os.getcwd(), "book")
os.makedirs(BOOKS_DIR, exist_ok=True)  # Ensure the book folder exists

class BookScannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Book Page Scanner")

        # ---------- Language Selector ----------
        self.language = tk.StringVar(value="English")
        lang_frame = tk.Frame(root)
        lang_frame.pack(pady=5)
        tk.Label(lang_frame, text="Language:").pack(side=tk.LEFT, padx=5)
        tk.OptionMenu(lang_frame, self.language, *language_codes.keys()).pack(side=tk.LEFT)

        # ---------- Book Selector ----------
        self.book_var = tk.StringVar()
        self.new_book_entry = None
        self.book_frame = tk.Frame(root)
        self.book_frame.pack(pady=5)

        tk.Label(self.book_frame, text="Select Book:").pack(side=tk.LEFT, padx=5)

        self.book_options = self.get_existing_books() + ["-- New Book --"]
        self.book_var.set(self.book_options[0] if self.book_options else "-- New Book --")
        self.book_menu = tk.OptionMenu(self.book_frame, self.book_var, *self.book_options, command=self.on_book_change)
        self.book_menu.pack(side=tk.LEFT)

        # ---------- Page Number ----------
        page_frame = tk.Frame(root)
        page_frame.pack(pady=5)
        tk.Label(page_frame, text="Page Number:").pack(side=tk.LEFT, padx=5)
        self.page_entry = tk.Entry(page_frame, width=5)
        self.page_entry.pack(side=tk.LEFT)
        self.page_entry.insert(0, "1")
        # ---------- Delete Book Button ----------

        self.delete_btn = tk.Button(root, text="🗑️ Delete Book", command=self.delete_book, height=2, width=20)
        self.delete_btn.pack(pady=5)

        # ---------- Live Preview ----------
        self.video_label = tk.Label(root)
        self.video_label.pack(pady=10)

        # ---------- Capture Button ----------
        self.capture_btn = tk.Button(root, text="📸 Capture Page", command=self.capture_page, height=2, width=20)
        self.capture_btn.pack(pady=10)

        # ---------- Camera Setup ----------
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Could not open camera")
            self.root.destroy()
            return

        self.cam_running = True
        self.start_camera_thread()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---------- Scan existing books in book/ folder ----------
    def get_existing_books(self):
        # Simply return all folders in BOOKS_DIR
        books = [folder for folder in os.listdir(BOOKS_DIR) if os.path.isdir(os.path.join(BOOKS_DIR, folder))]
        return sorted(books)

    # ---------- Handle book selection ----------
    def on_book_change(self, selection):
        if selection == "-- New Book --" and self.new_book_entry is None:
            self.new_book_entry = tk.Entry(self.book_frame)
            self.new_book_entry.pack(side=tk.LEFT, padx=5)
        # If another book is selected, remove entry box
        elif selection != "-- New Book --" and self.new_book_entry is not None:
            self.new_book_entry.destroy()
            self.new_book_entry = None

    def delete_book(self):
        book_name = self.book_var.get()

        # Prevent deleting if "-- New Book --" is selected
        if book_name == "-- New Book --":
            messagebox.showerror("Error", "Please select an existing book to delete.")
            return

        folder_path = os.path.join(BOOKS_DIR, book_name)
        if not os.path.exists(folder_path):
            messagebox.showerror("Error", "Book folder does not exist.")
            return

        # Count number of pages/files
        num_pages = len([f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))])

        # Ask for confirmation
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"The book '{book_name}' has {num_pages} page(s).\nAre you sure you want to delete it?"
        )
        if confirm:
            shutil.rmtree(folder_path)
            messagebox.showinfo("Deleted", f"Book '{book_name}' has been deleted.")

            # Refresh dropdown
            self.book_options = self.get_existing_books() + ["-- New Book --"]
            menu = self.book_menu["menu"]
            menu.delete(0, "end")
            for book in self.book_options:
                menu.add_command(label=book, command=lambda value=book: self.book_var.set(value))
            # Select first book or new book option
            self.book_var.set(self.book_options[0] if self.book_options else "-- New Book --")

    # ---------- Camera Thread ----------
    def start_camera_thread(self):
        threading.Thread(target=self.camera_loop, daemon=True).start()

    def camera_loop(self):
        while self.cam_running:
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.resize(frame, (480, 360))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(img)
                self.video_label.after(0, self.update_label_image, imgtk)

    def update_label_image(self, imgtk):
        self.video_label.imgtk = imgtk
        self.video_label.configure(image=imgtk)

    # ---------- Capture Page ----------
    def capture_page(self):
        # Determine book name
        book_name = self.book_var.get()
        is_new = False
        if book_name == "-- New Book --":
            if self.new_book_entry is None or not self.new_book_entry.get().strip():
                messagebox.showerror("Error", "Enter a valid book title")
                return
            book_name = self.new_book_entry.get().strip()
            is_new = True

        page_number = self.page_entry.get().strip()
        lang_code = language_codes[self.language.get()]

        if not page_number.isdigit():
            messagebox.showerror("Error", "Enter a valid page number")
            return

        # Folder name inside book/
        folder_name = f"{book_name}_{lang_code}"
        folder = os.path.join(BOOKS_DIR, folder_name)
        os.makedirs(folder, exist_ok=True)

        filename = f"{book_name}_{page_number}.jpg"
        filepath = os.path.join(folder, filename)

        # Avoid overwrite
        counter = 1
        while os.path.exists(filepath):
            filepath = os.path.join(folder, f"{book_name}_{page_number}_{counter}.jpg")
            counter += 1

        ret, frame = self.cap.read()
        if ret:
            cv2.imwrite(filepath, frame)
            messagebox.showinfo("Saved", f"Saved {os.path.basename(filepath)} in {folder_name}")
            self.page_entry.delete(0, tk.END)
            self.page_entry.insert(0, str(int(page_number) + 1))

            # If new book, update dropdown and select it
            if is_new:
                self.refresh_book_dropdown(folder_name)

        else:
            messagebox.showerror("Error", "Failed to capture image")

    # ---------- Refresh book dropdown ----------
    def refresh_book_dropdown(self, new_book_name):
        self.book_options = self.get_existing_books() + ["-- New Book --"]
        menu = self.book_menu["menu"]
        menu.delete(0, "end")
        for book in self.book_options:
            menu.add_command(label=book, command=lambda value=book: self.book_var.set(value))

        # Select the newly created book in the dropdown
        self.book_var.set(new_book_name)

        # Remove old entry box if it exists
        if self.new_book_entry is not None:
            self.new_book_entry.destroy()

        # Create a new entry box for adding another book
        self.new_book_entry = tk.Entry(self.book_frame)
        self.new_book_entry.pack(side=tk.LEFT, padx=5)

        # Set dropdown back to "-- New Book --" for convenience
        self.book_var.set("-- New Book --")

    # ---------- Cleanup ----------
    def on_close(self):
        self.cam_running = False
        if hasattr(self, "cap") and self.cap.isOpened():
            self.cap.release()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = BookScannerApp(root)
    root.mainloop()
