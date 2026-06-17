

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os

# ── Boje (BGR za OpenCV) ──────────────────────────────────────────────────────
COLOR_GREEN   = (0, 220, 80)
COLOR_BLUE    = (220, 120, 0)
COLOR_ORANGE  = (0, 140, 255)
COLOR_RED     = (0, 60, 220)
COLOR_WHITE   = (255, 255, 255)
COLOR_BLACK   = (0, 0, 0)
COLOR_YELLOW  = (0, 210, 255)
COLOR_GRAY    = (150, 150, 150)
COLOR_TEAL    = (180, 200, 0)
COLOR_PURPLE  = (200, 80, 180)

# ── Emoji font ────────────────────────────────────────────────────────────────
_EMOJI_FONT = None
_EMOJI_FONT_PATH = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

def _get_emoji_font():
    global _EMOJI_FONT
    if _EMOJI_FONT is None and os.path.exists(_EMOJI_FONT_PATH):
        try:
            _EMOJI_FONT = ImageFont.truetype(
                _EMOJI_FONT_PATH, 109,
                layout_engine=ImageFont.Layout.BASIC
            )
        except Exception:
            _EMOJI_FONT = None
    return _EMOJI_FONT

def draw_emoji_on_frame(frame, emoji_str: str, x: int, y: int, size: int = 28):
    """Crta emoji na OpenCV frame korištenjem PIL."""
    font = _get_emoji_font()
    if font is None:
        return

    render_sz = 109
    canvas = Image.new("RGBA", (render_sz + 10, render_sz + 10), (0, 0, 0, 0))
    draw   = ImageDraw.Draw(canvas)
    draw.text((0, 0), emoji_str, font=font, embedded_color=True)

    canvas = canvas.resize((size, size), Image.LANCZOS)

    h_f, w_f = frame.shape[:2]
    x1, y1 = x, y
    x2, y2 = x + size, y + size

    cx1 = max(0, -x1);  cy1 = max(0, -y1)
    cx2 = size - max(0, x2 - w_f)
    cy2 = size - max(0, y2 - h_f)
    x1  = max(0, x1);   y1 = max(0, y1)
    x2  = min(w_f, x2); y2 = min(h_f, y2)

    if x2 <= x1 or y2 <= y1:
        return

    region = frame[y1:y2, x1:x2].astype(np.float32)
    patch  = np.array(canvas)[cy1:cy2, cx1:cx2]

    rgb_patch = patch[:, :, :3][:, :, ::-1].astype(np.float32)
    alpha     = patch[:, :, 3:4].astype(np.float32) / 255.0

    blended = rgb_patch * alpha + region * (1.0 - alpha)
    frame[y1:y2, x1:x2] = blended.astype(np.uint8)

# ── Pomočne funkcije ──────────────────────────────────────────────────────────

def draw_rounded_rect(frame, x, y, w, h, r, color, alpha=0.6):
    overlay = frame.copy()
    cv2.rectangle(overlay, (x + r, y), (x + w - r, y + h), color, -1)
    cv2.rectangle(overlay, (x, y + r), (x + w, y + h - r), color, -1)
    for cx, cy in [(x+r, y+r), (x+w-r, y+r), (x+r, y+h-r), (x+w-r, y+h-r)]:
        cv2.circle(overlay, (cx, cy), r, color, -1)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

def draw_text_with_shadow(frame, text, pos, font_scale=0.8, color=COLOR_WHITE,
                          thickness=2, font=cv2.FONT_HERSHEY_DUPLEX):
    x, y = pos
    cv2.putText(frame, text, (x+2, y+2), font, font_scale,
                COLOR_BLACK, thickness + 1, cv2.LINE_AA)
    cv2.putText(frame, text, (x, y), font, font_scale,
                color, thickness, cv2.LINE_AA)

def draw_progress_bar(frame, progress, x, y, w, h):
    cv2.rectangle(frame, (x, y), (x + w, y + h), COLOR_GRAY, -1)
    fill_w = int(w * progress)
    if fill_w > 0:
        color = COLOR_GREEN if progress < 0.8 else COLOR_YELLOW
        cv2.rectangle(frame, (x, y), (x + fill_w, y + h), color, -1)
    cv2.rectangle(frame, (x, y), (x + w, y + h), COLOR_WHITE, 1)

def draw_no_hand_warning(frame):
    h, w = frame.shape[:2]
    draw_rounded_rect(frame, w//2 - 160, 45, 320, 32, 8, (0, 0, 100), 0.7)
    draw_text_with_shadow(frame, "! Ruka nije detektirana",
                          (w//2 - 140, 68), font_scale=0.6,
                          color=COLOR_ORANGE, thickness=1)

def draw_timer_big(frame, secs: float):
    """Veliki tajmer prikaz kad je manje od 10s."""
    if secs > 15:
        return
    h, w = frame.shape[:2]
    color = COLOR_RED if secs < 10 else COLOR_YELLOW
    text  = f"{int(secs)}"
    draw_rounded_rect(frame, w//2 - 45, h//2 - 55, 90, 70, 12, (0, 0, 60), 0.7)
    draw_text_with_shadow(frame, text, (w//2 - 25, h//2 + 5),
                          font_scale=2.2, color=color, thickness=4)

# ── Glavni overlay elementi ───────────────────────────────────────────────────

def draw_game_panel(frame, status: dict):
    h, w = frame.shape[:2]
    panel_h = 116
    panel_y = h - panel_h

    draw_rounded_rect(frame, 0, panel_y, w, panel_h, 0, (20, 20, 20), 0.78)

    # Izraz
    draw_text_with_shadow(frame, f"Izraz: {status['expression_str']}", (15, panel_y + 35),
                          font_scale=0.95, color=COLOR_YELLOW, thickness=2)

    # Bodovi
    draw_text_with_shadow(frame, f"Bodovi: {status['score']}", (15, panel_y + 68),
                          font_scale=0.7, color=COLOR_GREEN, thickness=2)

    # Trenutni input
    fingers = status.get('current_fingers', -1)
    gesture = status.get('current_gesture')
    input_text = f"Prsti: {fingers}" if fingers >= 0 else ("Gesta: " + (gesture if gesture else "?"))
    draw_text_with_shadow(frame, input_text, (15, panel_y + 95),
                          font_scale=0.55, color=COLOR_WHITE, thickness=1)

    # Tezina (ASCII formating)
    diff = status.get('difficulty_name', '').upper()
    diff_color = {
        "LAGANO": COLOR_GREEN, "SREDNJE": COLOR_ORANGE, "TESKO": COLOR_RED
    }.get(diff, COLOR_WHITE)
    draw_text_with_shadow(frame, f"[{diff}]", (w - 150, panel_y + 35),
                          font_scale=0.65, color=diff_color, thickness=2)

    # Tajmer
    t = status["time_remaining"]
    if t is not None:
        t_color = COLOR_RED if t < 5 else (COLOR_YELLOW if t < 10 else COLOR_WHITE)
        draw_text_with_shadow(frame, f"Vrijeme: {int(t)}s",
                              (w - 150, panel_y + 68),
                              font_scale=0.65, color=t_color, thickness=2)

    # Hold progress bar
    progress = status["hold_progress"]
    if progress > 0:
        draw_progress_bar(frame, progress, 0, h - 8, w, 8)
        draw_text_with_shadow(frame, f"Drzi... {int(progress*100)}%",
                              (w - 160, panel_y + 110),
                              font_scale=0.5, color=COLOR_YELLOW, thickness=1)

def draw_game_over_overlay(frame, status: dict):
    h, w = frame.shape[:2]
    draw_rounded_rect(frame, w//2 - 230, h//2 - 105, 460, 210, 18, (10, 10, 60), 0.9)
    cv2.rectangle(frame, (w//2 - 230, h//2 - 105), (w//2 + 230, h//2 + 105), COLOR_RED, 2)

    draw_text_with_shadow(frame, "GAME OVER", (w//2 - 110, h//2 - 55),
                          font_scale=1.3, color=COLOR_RED, thickness=3)

    # Replaced special chars for standard ASCII
    reason = status.get("fail_reason", "Isteklo vrijeme!")
    draw_text_with_shadow(frame, reason, (w//2 - 180, h//2),
                          font_scale=0.85, color=COLOR_YELLOW, thickness=2)

    draw_text_with_shadow(frame, f"Bodovi: {status['score']}",
                          (w//2 - 70, h//2 + 40),
                          font_scale=0.8, color=COLOR_WHITE, thickness=2)

    draw_text_with_shadow(frame, "Odaberi opciju ->",
                          (w//2 - 110, h//2 + 85),
                          font_scale=0.6, color=COLOR_GRAY, thickness=1)