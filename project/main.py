"""
Hand Gesture Calculator - Glavni pokretac aplikacije
"""

import sys


def check_dependencies():
    missing = []
    try:
        import cv2
    except ImportError:
        missing.append("opencv-python")
    try:
        import mediapipe
    except ImportError:
        missing.append("mediapipe")
    try:
        import numpy
    except ImportError:
        missing.append("numpy")
    try:
        import PIL
    except ImportError:
        missing.append("Pillow")
    try:
        import tkinter
    except ImportError:
        missing.append("tkinter (ugraden u Python, provjeri instalaciju)")

    if missing:
        print("Nedostaju paketi. Instaliraj ih naredbom:")
        print(f"   pip install {' '.join(p for p in missing if p != 'tkinter (ugraden u Python, provjeri instalaciju)')}")
        sys.exit(1)
    print("Svi paketi su dostupni.")


if __name__ == "__main__":
    check_dependencies()

    import tkinter as tk
    from gui import show_difficulty_screen_proper

    root = tk.Tk()
    root.title("Hand Gesture Calculator")
    root.configure(bg="#0d0d1a")
    root.resizable(False, False)

    # Postavi minimalnu velicinu
    root.minsize(960, 620)

    show_difficulty_screen_proper(root)

    root.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()
