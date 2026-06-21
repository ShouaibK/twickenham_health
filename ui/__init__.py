import os
import tkinter as tk

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None


def _get_project_logo_path():
    base = os.path.dirname(os.path.dirname(__file__))
    candidates = [
        "twickenham_health_logo.png",
        "logo.png",
        "logo.jpg",
        "logo.jpeg",
    ]
    for name in candidates:
        path = os.path.join(base, "assets", name)
        if os.path.exists(path):
            return path
    return None


def load_logo_image(size=None):
    path = _get_project_logo_path()
    if not path:
        return None

    if size and Image and ImageTk:
        try:
            img = Image.open(path)
            img = img.convert("RGBA")
            img = img.resize(size, Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception:
            pass

    try:
        return tk.PhotoImage(file=path)
    except tk.TclError:
        return None
