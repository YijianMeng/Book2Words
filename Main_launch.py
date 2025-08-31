import tkinter as tk
import subprocess
import sys
import os

def run_scanner():
    """Run the Book Scanner GUI"""
    python = sys.executable
    script = os.path.join(os.getcwd(), "ImageCaptureApple.py")
    subprocess.Popen([python, script])

def run_translator():
    """Run the Translator/PDF GUI"""
    python = sys.executable
    script = os.path.join(os.getcwd(), "Image2Words_GUI.py")
    subprocess.Popen([python, script])

class MainLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Book Tools Launcher")
        self.root.geometry("300x200")

        tk.Label(root, text="📚 Choose Tool", font=("Arial", 14, "bold")).pack(pady=20)

        tk.Button(root, text="📸 Book Scanner", width=20, height=2, command=run_scanner).pack(pady=10)
        tk.Button(root, text="🌍 Translator & PDF", width=20, height=2, command=run_translator).pack(pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = MainLauncher(root)
    root.mainloop()
