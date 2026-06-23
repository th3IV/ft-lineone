import tkinter as tk
from tkinter import simpledialog
import re, os

root = tk.Tk()
root.withdraw()

key = simpledialog.askstring("Google AI API Key", "Pega tu API key (AIzaSy...):")

if key and key.strip():
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    with open(env_path, "r") as f:
        content = f.read()
    content = re.sub(r"GOOGLE_AI_API_KEY=.*", f"GOOGLE_AI_API_KEY={key.strip()}", content)
    with open(env_path, "w") as f:
        f.write(content)
    print("OK! GOOGLE_AI_API_KEY actualizada")
else:
    print("No se ingreso ninguna clave")
