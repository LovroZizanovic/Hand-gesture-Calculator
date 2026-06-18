"""
gui.py - Moderni Tkinter GUI s odabirom tezine i video streamom
"""

import tkinter as tk
from tkinter import ttk
import cv2
import numpy as np
from PIL import Image, ImageTk
import threading
import time

from hand_detector import HandDetector
from calculator import GameSession, GameDifficulty, GameState
import overlay as ov

BG_DARK     = "#0d0d1a"
BG_CARD     = "#161628"
BG_PANEL    = "#1e1e38"
ACCENT_PINK = "#e94560"
ACCENT_TEAL = "#4ecca3"
ACCENT_GOLD = "#ffd700"
TEXT_MAIN   = "#e8e8f0"
TEXT_DIM    = "#7a7a9a"
TEXT_GREEN  = "#3ddc84"
TEXT_RED    = "#ff6b6b"
TEXT_ORANGE = "#ffaa44"

DIFFICULTY_MAP = {
    "Lagano":  GameDifficulty.EASY,
    "Srednje": GameDifficulty.MEDIUM,
    "Tesko":   GameDifficulty.HARD,
}

def _lighten(hex_color):
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
    return f"#{min(255,r+30):02x}{min(255,g+30):02x}{min(255,b+30):02x}"

def styled_button(parent, text, color, cmd, width=12):
    btn = tk.Button(
        parent, text=text, bg=color, fg=BG_DARK,
        font=("Segoe UI", 11, "bold"),
        relief="flat", bd=0, cursor="hand2",
        activebackground=color, activeforeground=BG_DARK,
        width=width, pady=7, command=cmd
    )
    btn.bind("<Enter>", lambda e: btn.config(bg=_lighten(color)))
    btn.bind("<Leave>", lambda e: btn.config(bg=color))
    return btn


class DifficultyScreen(tk.Frame):

    def __init__(self, parent, on_select):
        super().__init__(parent, bg=BG_DARK)
        self.on_select = on_select
        self._build()

    def _build(self):
        self.pack(fill="both", expand=True)

        tk.Label(self, text="Hand Gesture Calculator", font=("Segoe UI", 28, "bold"),
                 fg=ACCENT_PINK, bg=BG_DARK).pack(pady=(50, 6))

        tk.Label(self, text="Dostigni zadani ciljni broj gradeci izraz rukama!",
                 font=("Segoe UI", 12), fg=TEXT_DIM, bg=BG_DARK).pack(pady=(0, 40))

        tk.Label(self, text="ODABERI TEZINU", font=("Segoe UI", 13, "bold"),
                 fg=ACCENT_TEAL, bg=BG_DARK).pack(pady=(0, 20))

        cards_frame = tk.Frame(self, bg=BG_DARK)
        cards_frame.pack()

        difficulties = [
            ("LAGANO", "Bez tajmera", TEXT_GREEN, "#0d2a1a",
             "Slobodan unos.\nIzgradi izraz gestama,\nprogram racuna.", "Lagano"),
            ("SREDNJE", "2 broja • 1 operacija •  25s", TEXT_ORANGE, "#2a1a00",
             "Prikazuje se meta.\nSlozi izraz s 2 broja \nda dosegnes cilj u vremenu.", "Srednje"),
            ("TESKO", "3 broja • 2 operacije  •  20s", TEXT_RED, "#2a0000",
             "Prikazuje se meta.\nSlozi izraz s 3 broja \nda dosegnes cilj brzo!", "Tesko"),
        ]

        for title, subtitle, color, bg, desc, key in difficulties:
            card = tk.Frame(cards_frame, bg=bg, padx=22, pady=18,
                            highlightbackground=color, highlightthickness=2)
            card.pack(side="left", padx=14, fill="y")

            tk.Label(card, text=title, font=("Segoe UI", 17, "bold"), fg=color, bg=bg).pack()
            tk.Label(card, text=subtitle, font=("Segoe UI", 10), fg=TEXT_DIM, bg=bg).pack(pady=(2, 8))
            tk.Label(card, text=desc, font=("Segoe UI", 9), fg=TEXT_MAIN, bg=bg, justify="center").pack(pady=(0, 14))

            tk.Button(card, text=f"  Igraj {title}  ", bg=color, fg=BG_DARK, font=("Segoe UI", 10, "bold"),
                      relief="flat", bd=0, cursor="hand2", pady=7, padx=12,
                      command=lambda k=key: self.on_select(k)).pack()
            
        tk.Label(self, text="Fakultet elektrotehnike, računarstva i informacijskih tehnologija", font=("Segoe UI", 10, "bold"),
                 fg=TEXT_DIM, bg=BG_DARK).pack(pady=(50, 0))
        tk.Label(self, text="Studij: Robotika i umjetna inteligencija", font=("Segoe UI", 8),
                 fg=TEXT_DIM, bg=BG_DARK).pack(pady=(0, 5))
        tk.Label(self, text="Kolegij: Robotski vid", font=("Segoe UI", 8),
                 fg=TEXT_DIM, bg=BG_DARK).pack(pady=(0, 5))
        tk.Label(self, text="Izradili: Luka Idžanović, Lovro Žižanović, Nina Sučić, Dino Veršić", font=("Segoe UI", 8),
                 fg=TEXT_DIM, bg=BG_DARK).pack(pady=(0, 5))
        tk.Label(self, text="Mentor: doc. dr. sc. Petra Pejić", font=("Segoe UI", 8),
                 fg=TEXT_DIM, bg=BG_DARK).pack(pady=(0, 5))
            
            


class CalculatorApp(tk.Frame):

    VIDEO_W    = 640
    VIDEO_H    = 480
    FPS_TARGET = 30

    def __init__(self, parent: tk.Tk, difficulty: str):
        super().__init__(parent, bg=BG_DARK)
        self.root       = parent
        self.difficulty = difficulty

        self.detector = HandDetector()
        self.session  = GameSession(DIFFICULTY_MAP[difficulty])

        self.cap            = None
        self.running        = False
        self._frame_thread  = None
        self._current_photo = None
        self._game_over_shown = False

        self._build_ui()
        self.pack(fill="both", expand=True)

    def _build_ui(self):
        header = tk.Frame(self, bg="#0a0a18", pady=8)
        header.pack(fill="x")

        tk.Label(header, text="Hand Gesture Calculator", font=("Segoe UI", 17, "bold"),
                 fg=ACCENT_PINK, bg="#0a0a18").pack(side="left", padx=18)

        diff_color = {"Lagano": TEXT_GREEN, "Srednje": TEXT_ORANGE, "Tesko": TEXT_RED}.get(self.difficulty, TEXT_MAIN)
        tk.Label(header, text=f"[{self.difficulty.upper()}]", font=("Segoe UI", 11, "bold"),
                 fg=diff_color, bg="#0a0a18").pack(side="left")

        self.score_var = tk.StringVar(value="Bodovi: 0")
        tk.Label(header, textvariable=self.score_var, font=("Segoe UI", 12, "bold"),
                 fg=TEXT_GREEN, bg="#0a0a18").pack(side="left", padx=14)

        timer_txt = f"Vrijeme: {int(self.session.time_limit)}s" if self.session.time_limit else "Bez tajmera"
        self.timer_var = tk.StringVar(value=timer_txt)
        tk.Label(header, textvariable=self.timer_var, font=("Segoe UI", 11, "bold"),
                 fg=ACCENT_GOLD, bg="#0a0a18").pack(side="left", padx=14)

        self.fps_var = tk.StringVar(value="FPS: --")
        tk.Label(header, textvariable=self.fps_var, font=("Courier", 9), fg=TEXT_DIM, bg="#0a0a18").pack(side="right", padx=12)

        content = tk.Frame(self, bg=BG_DARK)
        content.pack(fill="both", expand=True, padx=10, pady=8)

        vid_wrap = tk.Frame(content, bg=ACCENT_PINK, bd=2)
        vid_wrap.pack(side="left")
        self.video_label = tk.Label(vid_wrap, bg=BG_DARK)
        self.video_label.pack(padx=2, pady=2)
        placeholder = np.zeros((self.VIDEO_H, self.VIDEO_W, 3), dtype=np.uint8)
        ov.draw_text_with_shadow(placeholder, "Pritisni Start za pokretanje kamere", (50, self.VIDEO_H // 2), 0.8, ov.COLOR_GRAY, 2)
        self._show_frame(placeholder)

        self._build_game_over_overlay(vid_wrap)

        right = tk.Frame(content, bg=BG_DARK, width=310)
        right.pack(side="left", fill="y", padx=(12, 0))
        right.pack_propagate(False)

        self._card(right, "CILJ").pack(fill="x", pady=(0, 8))
        self.target_var = tk.StringVar(value="")
        tk.Label(self._last_body, textvariable=self.target_var, font=("Segoe UI", 26, "bold"),
                 fg=ACCENT_TEAL, bg=BG_CARD, pady=6, justify="center").pack(fill="x")

        self._card(right, "TVOJ IZRAZ").pack(fill="x", pady=(0, 8))
        self.expr_var = tk.StringVar(value="_ ? _")
        
        self.expr_label = tk.Label(self._last_body, textvariable=self.expr_var, font=("Segoe UI", 20, "bold"),
                 fg=ACCENT_GOLD, bg=BG_CARD, pady=6, justify="center")
        self.expr_label.pack(fill="x")

        self.status_var = tk.StringVar(value="Kamera nije pokrenuta")
        tk.Label(self._last_body, textvariable=self.status_var, font=("Segoe UI", 9), fg=ACCENT_TEAL, bg=BG_CARD,
                 wraplength=270, justify="left", padx=8, pady=3).pack(fill="x")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("M.Horizontal.TProgressbar", troughcolor=BG_PANEL, background=ACCENT_TEAL,
                         bordercolor=BG_CARD, lightcolor=ACCENT_TEAL, darkcolor=ACCENT_TEAL, thickness=10)
        self.progress_var = tk.DoubleVar(value=0.0)
        ttk.Progressbar(self._last_body, variable=self.progress_var, maximum=1.0, length=270,
                        style="M.Horizontal.TProgressbar").pack(padx=8, pady=(4, 6))

        self._card(right, "PRAVILA").pack(fill="x", pady=(0, 8))
        
        # NOVO: Dinamički promijenjen tekst s objašnjenjem gesti, emoji znakovima i fokusom na niz bodova
        gestures_legend = "GESTE:\nSaka (zatvorena) = (+)\nV-znak (2 prsta) = (-)\nPalac = (*)\nPalac+Mali prst = (/)\n\n"
        
        rules_text = {
            "Lagano":  gestures_legend + "Dosegni cilj! Unesi Broj -> Gestu -> Broj.\nProgram racuna slobodan unos.",
            "Srednje": gestures_legend + "Dosegni cilj! \nDrzi ruku 1.5s.\nOstvari sto veci niz!",
            "Tesko":   gestures_legend + "Dosegni cilj! \nSpajaj tri broja.\nOstvari sto veci niz!"
        }.get(self.difficulty, "")
        
        tk.Label(self._last_body, text=rules_text, font=("Segoe UI", 9), fg=ACCENT_GOLD, bg=BG_CARD,
                 pady=6, padx=8, justify="left").pack(fill="x")

        self._card(right, "POVIJEST").pack(fill="both", expand=True, pady=(0, 8))
        self.history_var = tk.StringVar(value="")
        tk.Label(self._last_body, textvariable=self.history_var, font=("Consolas", 8), fg=TEXT_DIM, bg=BG_CARD,
                 pady=4, padx=8, justify="left", anchor="nw", wraplength=270).pack(fill="both", expand=True)

        btn_bar = tk.Frame(self, bg="#0a0a18", pady=8)
        btn_bar.pack(fill="x", side="bottom")

        self.btn_start = styled_button(btn_bar, "Start", ACCENT_TEAL, self._start_camera)
        self.btn_start.pack(side="left", padx=10)

        self.btn_stop = styled_button(btn_bar, "Stop", ACCENT_PINK, self._stop_camera)
        self.btn_stop.config(state="disabled")
        self.btn_stop.pack(side="left", padx=4)

        styled_button(btn_bar, "Restart", TEXT_ORANGE, self._try_again).pack(side="left", padx=4)
        styled_button(btn_bar, "< Nazad", TEXT_DIM, self._go_back).pack(side="left", padx=4)
        styled_button(btn_bar, "Izlaz", "#555555", self._on_close).pack(side="right", padx=10)

    def _card(self, parent, title):
        frame = tk.Frame(parent, bg=BG_CARD, highlightbackground="#2a2a4a", highlightthickness=1)
        tk.Label(frame, text=title, font=("Segoe UI", 8, "bold"), fg=ACCENT_PINK, bg=BG_CARD, anchor="w", padx=8, pady=3).pack(fill="x")
        tk.Frame(frame, bg="#2a2a4a", height=1).pack(fill="x")
        body = tk.Frame(frame, bg=BG_CARD)
        body.pack(fill="x")
        self._last_body = body
        return frame

    def _build_game_over_overlay(self, vid_wrap):
        self.game_over_frame = tk.Frame(vid_wrap, bg="#10102a", highlightbackground=ACCENT_PINK, highlightthickness=2)

        self.go_title_lbl = tk.Label(self.game_over_frame, text="GAME OVER", font=("Segoe UI", 24, "bold"), fg=TEXT_RED, bg="#10102a")
        self.go_title_lbl.pack(pady=(24, 6))

        self.game_over_info_var = tk.StringVar()
        tk.Label(self.game_over_frame, textvariable=self.game_over_info_var, font=("Segoe UI", 13), fg=ACCENT_GOLD, bg="#10102a").pack(pady=(0, 6))

        self.game_over_score_var = tk.StringVar()
        tk.Label(self.game_over_frame, textvariable=self.game_over_score_var, font=("Segoe UI", 12, "bold"), fg=TEXT_MAIN, bg="#10102a").pack(pady=(0, 18))

        btns = tk.Frame(self.game_over_frame, bg="#10102a")
        btns.pack(pady=(0, 24))

        styled_button(btns, "Try Again", ACCENT_TEAL, self._try_again, 12).pack(side="left", padx=10)
        styled_button(btns, "Homepage", TEXT_DIM, self._go_back, 12).pack(side="left", padx=10)

    def _show_game_over(self):
        status = self.session._status()
        self.game_over_info_var.set(status.get("fail_reason", "Isteklo vrijeme!"))
        self.game_over_score_var.set(f"Bodovi: {status['score']}")
        self.game_over_frame.place(relx=0.5, rely=0.5, anchor="center")

    def _hide_game_over(self):
        self.game_over_frame.place_forget()

    def _start_camera(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.status_var.set("Kamera nije pronadena!")
            return
        
        self.session.reset_round_timer()
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.VIDEO_W)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.VIDEO_H)
        self.running = True
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")

        self._frame_thread = threading.Thread(target=self._video_loop, daemon=True)
        self._frame_thread.start()

    def _stop_camera(self):
        self.running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
        self.status_var.set("Kamera zaustavljena")
        placeholder = np.zeros((self.VIDEO_H, self.VIDEO_W, 3), dtype=np.uint8)
        ov.draw_text_with_shadow(placeholder, "Kamera zaustavljena", (180, self.VIDEO_H // 2), 0.9, ov.COLOR_GRAY, 2)
        self._show_frame(placeholder)

    def _video_loop(self):
        fps_counter = 0
        fps_timer   = time.time()

        while self.running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret: break
            frame = cv2.flip(frame, 1)

            hands = self.detector.find_hands(frame, draw=True)
            fingers = -1
            gesture = None

            if hands:
                fingers = self.detector.count_fingers(hands[0])
                gesture = self.detector.detect_gesture(hands[0])
            else:
                ov.draw_no_hand_warning(frame)

            if self.session.game_state == GameState.PLAYING:
                status = self.session.update(fingers, gesture)
            else:
                status = self.session._status()
                if not self._game_over_shown:
                    self._game_over_shown = True
                    self.root.after(0, self._show_game_over)

            status["current_fingers"] = fingers
            status["current_gesture"] = gesture
            ov.draw_game_panel(frame, status)

            if status["game_state"] == GameState.PLAYING and status["time_remaining"] is not None and status["time_remaining"] <= 5 and not status.get("is_frozen", False):
                ov.draw_timer_big(frame, status["time_remaining"])

            fps_counter += 1
            if time.time() - fps_timer >= 1.0:
                self.fps_var.set(f"FPS: {fps_counter}")
                fps_counter = 0
                fps_timer = time.time()

            self.root.after(0, self._update_gui, frame, status)
            time.sleep(1 / self.FPS_TARGET)

    def _update_gui(self, frame, status):
        self._show_frame(frame)
        
        if self.running:
            if status.get("target") is not None:
                self.target_var.set(f"CILJ: {status['target']}")
            else:
                self.target_var.set("FREESTYLE")
        else:
            self.target_var.set("")
            
        self.expr_var.set(status["expression_str"])
        
        if status.get("is_frozen", False):
            self.expr_label.config(fg=TEXT_GREEN)
        else:
            self.expr_label.config(fg=ACCENT_GOLD)

        self.status_var.set(status["instruction"])
        self.progress_var.set(status["hold_progress"])
        self.score_var.set(f"Bodovi: {status['score']}")

        t = status["time_remaining"]
        if t is not None:
            self.timer_var.set(f"Vrijeme: {int(t)}s")
        else:
            self.timer_var.set("Bez tajmera")

        if status["history"]:
            self.history_var.set("\n".join(status["history"][-6:]))

    def _show_frame(self, frame):
        rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img   = Image.fromarray(rgb)
        img   = img.resize((self.VIDEO_W, self.VIDEO_H))
        photo = ImageTk.PhotoImage(image=img)
        self.video_label.config(image=photo)
        self._current_photo = photo

    def _try_again(self):
        self.session.restart()
        self.session.reset_round_timer()
        self._game_over_shown = False
        self._hide_game_over()
        self.status_var.set("Igra restartana")

    def _go_back(self):
        self._stop_camera()
        self.pack_forget()
        self.destroy()
        show_difficulty_screen_proper(self.root)

    def _on_close(self):
        self._stop_camera()
        self.root.destroy()


def show_difficulty_screen_proper(root: tk.Tk):
    for widget in root.winfo_children():
        widget.destroy()

    def on_select(difficulty: str):
        for widget in root.winfo_children():
            widget.destroy()
        CalculatorApp(root, difficulty)

    DifficultyScreen(root, on_select)
