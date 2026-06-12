# Floating card rendering, hit testing, and mouse interaction (pure)

import cv2
import numpy as np

from state import CARD_W, CARD_H

C_AMBER    = (61,  163, 232)
C_GRAY_L   = (82,  88,  90)
C_BORDER_I = (53,  57,  58)
C_RED      = (49,  75,  200)
C_BG       = (10,  10,  10)

FONT  = cv2.FONT_HERSHEY_PLAIN
FS    = 0.75   # card text scale
PAD   = 4
HEADER_H = 14
FOOTER_H = 12
IMG_H    = CARD_H - HEADER_H - FOOTER_H - PAD * 3


def render_cards(frame: np.ndarray, state: dict) -> np.ndarray:
    """Draw all capture cards onto frame. Pure."""
    out = frame.copy()
    fc = state["frame_count"]
    drag_id = state["drag_card_id"]
    # Draw inactive cards first, active card on top
    for card in state["cards"]:
        if card["id"] == drag_id:
            continue
        pos = _lerp_pos(card, fc)
        _render_single_card(out, card, pos, is_active=False)
    if drag_id is not None:
        for card in state["cards"]:
            if card["id"] == drag_id:
                _render_single_card(out, card, card["pos"], is_active=True)
                break
    return out


def hit_test_card_body(card: dict, pos: tuple, mx: int, my: int) -> bool:
    px, py = pos
    return px <= mx <= px + CARD_W and py <= my <= py + CARD_H


def hit_test_delete_btn(card: dict, pos: tuple, mx: int, my: int) -> bool:
    """[X] is in the bottom-right corner of the card."""
    px, py = pos
    bx1 = px + CARD_W - 22
    by1 = py + CARD_H - FOOTER_H - PAD
    bx2 = px + CARD_W - PAD
    by2 = py + CARD_H - PAD
    return bx1 <= mx <= bx2 and by1 <= my <= by2


def get_card_pos(card: dict, frame_count: int) -> tuple:
    """Return the current animated position for a card."""
    return _lerp_pos(card, frame_count)


def get_card_at(cards: list, px: int, py: int, frame_count: int) -> dict | None:
    """Hit test: return top-most card at pixel (px, py), or None."""
    for card in reversed(cards):
        pos = _lerp_pos(card, frame_count)
        if hit_test_card_body(card, pos, px, py):
            return card
    return None


def move_card(card: dict, new_pos: tuple) -> dict:
    """Pure: return card with updated position."""
    return {**card, "pos": new_pos, "rest_pos": new_pos}


# ---------------------------------------------------------------------------
# Private
# ---------------------------------------------------------------------------

def _lerp_pos(card: dict, frame_count: int) -> tuple:
    t = min(1.0, (frame_count - card["spawn_frame"]) / 10.0)
    sx, sy = card["spawn_px"]
    rx, ry = card["rest_pos"]
    return (int(sx + t * (rx - sx)), int(sy + t * (ry - sy)))


def _render_single_card(out: np.ndarray, card: dict, pos: tuple, is_active: bool) -> None:
    px, py = pos
    h_frame, w_frame = out.shape[:2]

    # Clamp to frame
    px = max(0, min(px, w_frame - CARD_W))
    py = max(0, min(py, h_frame - CARD_H))

    x1, y1 = px, py
    x2, y2 = px + CARD_W, py + CARD_H

    # Background fill
    cv2.rectangle(out, (x1, y1), (x2, y2), C_BG, cv2.FILLED)

    # Border
    border_color = C_AMBER if is_active else C_BORDER_I
    cv2.rectangle(out, (x1, y1), (x2, y2), border_color, 1)

    # Header: label left, timestamp right
    header_y = y1 + HEADER_H - 1
    cv2.putText(out, card["label"], (x1 + PAD, header_y), FONT, FS, C_AMBER, 1, cv2.LINE_AA)
    (tw, _), _ = cv2.getTextSize(card["timestamp"], FONT, FS, 1)
    cv2.putText(out, card["timestamp"], (x2 - PAD - tw, header_y), FONT, FS, C_AMBER, 1, cv2.LINE_AA)

    # Divider line under header
    div_y = y1 + HEADER_H + 1
    cv2.line(out, (x1 + 1, div_y), (x2 - 1, div_y), border_color, 1)

    # Thumbnail
    img_y1 = div_y + 2
    img_y2 = y2 - FOOTER_H - PAD - 2
    img_x1 = x1 + PAD
    img_x2 = x2 - PAD
    img_w = img_x2 - img_x1
    img_h = img_y2 - img_y1
    if img_w > 0 and img_h > 0:
        img = card["image"]
        if img is not None and img.size > 0:
            thumb = cv2.resize(img, (img_w, img_h), interpolation=cv2.INTER_LINEAR)
            out[img_y1:img_y2, img_x1:img_x2] = thumb
        else:
            # Placeholder
            cv2.putText(out, "[ IMG ]", (img_x1 + 4, img_y1 + img_h // 2 + 4),
                        FONT, FS, C_BORDER_I, 1, cv2.LINE_AA)

    # Footer divider
    foot_div_y = y2 - FOOTER_H - PAD - 1
    cv2.line(out, (x1 + 1, foot_div_y), (x2 - 1, foot_div_y), border_color, 1)

    # Footer: label left, [X] right
    footer_y = y2 - PAD
    cv2.putText(out, "IMG", (x1 + PAD, footer_y), FONT, FS, C_GRAY_L, 1, cv2.LINE_AA)
    (xw, _), _ = cv2.getTextSize("[X]", FONT, FS, 1)
    cv2.putText(out, "[X]", (x2 - PAD - xw, footer_y), FONT, FS, C_RED, 1, cv2.LINE_AA)
