import tkinter as tk
from tkinter import messagebox
import cv2
import os
from PIL import Image, ImageTk


class BookScannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Book Page Scanner")

        # ---------- Input Frame ----------
        input_frame = tk.Frame(root)
        input_frame.pack(pady=10)

        tk.Label(input_frame, text="Book Name:").grid(row=0, column=0, padx=5, pady=5)
        self.book_entry = tk.Entry(input_frame)
        self.book_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(input_frame, text="Page Number:").grid(row=1, column=0, padx=5, pady=5)
        self.page_entry = tk.Entry(input_frame)
        self.page_entry.grid(row=1, column=1, padx=5, pady=5)
        self.page_entry.insert(0, "1")  # default start at page 1

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

        self.update_camera()

        # Handle window close properly
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def update_camera(self):
        ret, frame = self.cap.read()
        if ret:
            # Resize frame to smaller preview (e.g., 640x480)
            frame = cv2.resize(frame, (480, 360))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)

            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

        self.root.after(10, self.update_camera)  # keep updating

    def capture_page(self):
        book_name = self.book_entry.get().strip()
        page_number = self.page_entry.get().strip()

        if not book_name or not page_number.isdigit():
            messagebox.showerror("Error", "Enter a valid book name and page number")
            return

        folder = os.path.join(os.getcwd(), book_name)
        os.makedirs(folder, exist_ok=True)

        filename = f"{book_name}_{page_number}.jpg"
        filepath = os.path.join(folder, filename)

        # Avoid overwriting if page already exists
        counter = 1
        while os.path.exists(filepath):
            filepath = os.path.join(folder, f"{book_name}_{page_number}_{counter}.jpg")
            counter += 1

        ret, frame = self.cap.read()
        if ret:
            cv2.imwrite(filepath, frame)
            messagebox.showinfo("Saved", f"Saved {os.path.basename(filepath)}")

            # Auto-increment page
            self.page_entry.delete(0, tk.END)
            self.page_entry.insert(0, str(int(page_number) + 1))
        else:
            messagebox.showerror("Error", "Failed to capture image")

    def on_close(self):
        if hasattr(self, "cap") and self.cap.isOpened():
            self.cap.release()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = BookScannerApp(root)
    root.mainloop()
