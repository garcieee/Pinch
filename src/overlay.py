# Draw crop rectangle, landmarks, charge arc, HUD, and shutter flash onto frame (pure)

import time
import cv2
import numpy as np

# --- Palette (BGR) ---
C_AMBER    = (61,  163, 232)   # #E8A33D  active / values
C_GRAY_L   = (82,  88,  90)    # #5A5852  labels / keys
C_GRAY_M   = (112, 119, 122)   # #7A7770  reticles / mid
C_BORDER_I = (53,  57,  58)    # #3A3935  inactive borders
C_RED      = (49,  75,  200)   # #C84B31  destructive only

FONT    = cv2.FONT_HERSHEY_PLAIN
FS_SM   = 0.85   # small — labels, rulers
FS_MED  = 1.0    # medium — HUD text
FS_LG   = 1.1    # large — title


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def apply_base_style(frame: np.ndarray, state: dict) -> np.ndarray:
    """Draw the full HUD baseline onto a copy of frame. Pure."""
    out = frame.copy()
    h, w = out.shape[:2]
    _draw_ruler_ticks(out, h, w)
    _draw_top_left_info(out, state)
    _draw_top_right_info(out, state, w)
    _draw_bottom_left_tc(out, state, h)
    if (time.time() - state["legend_timer"]) < 3.0:
        _draw_gesture_legend(out, state, w, h)
    return out


def draw_crop_rect(frame: np.ndarray, state: dict) -> np.ndarray:
    """Draw crop rectangle + corner crosshairs + labels. Pure. SNAP mode only."""
    if state["mode"] != "snap":
        return frame
    if state["gesture"] != "framing" or state["framing_rect"] is None:
        return frame
    out = frame.copy()
    h, w = out.shape[:2]
    rect = state["framing_rect"]
    stable = state["stable_frames"] >= state["lock_threshold"]
    color = C_AMBER if stable else C_GRAY_M

    x1 = int(rect["x"] * w)
    y1 = int(rect["y"] * h)
    x2 = int((rect["x"] + rect["w"]) * w)
    y2 = int((rect["y"] + rect["h"]) * h)

    # Main rectangle
    cv2.rectangle(out, (x1, y1), (x2, y2), color, 1)

    # Corner crosshairs — 18px arms extending outward from each corner
    arm = 18
    corners = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
    dirs = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    for (cx, cy), (dx, dy) in zip(corners, dirs):
        cv2.line(out, (cx + dx * arm, cy), (cx, cy), color, 1)
        cv2.line(out, (cx, cy + dy * arm), (cx, cy), color, 1)

    # Dimension label above top-right corner
    pw = x2 - x1
    ph = y2 - y1
    dim_text = f"{pw:04d} x {ph:04d}"
    (tw, th), _ = cv2.getTextSize(dim_text, FONT, FS_MED, 1)
    cv2.putText(out, dim_text, (x2 - tw, y1 - 6), FONT, FS_MED, C_AMBER, 1, cv2.LINE_AA)

    # Stability countdown below bottom-left corner
    lock_in = state.get("lock_in_secs")
    if not stable and lock_in is not None:
        lock_text = f"LOCK IN {lock_in:04.1f}s"
        cv2.putText(out, lock_text, (x1, y2 + 14), FONT, FS_SM, C_GRAY_M, 1, cv2.LINE_AA)

    return out


def draw_fingertip_markers(frame: np.ndarray, state: dict) -> np.ndarray:
    """Draw crosshair + circle at thumb and index tips. Pure."""
    if state["gesture"] == "idle":
        return frame
    out = frame.copy()
    h, w = out.shape[:2]
    tips = state["thumb_tips"] + state["index_tips"]
    for tip in tips:
        px = int(tip["x"] * w)
        py = int(tip["y"] * h)
        cv2.circle(out, (px, py), 12, C_GRAY_M, 1, cv2.LINE_AA)
        cv2.line(out, (px - 8, py), (px + 8, py), C_GRAY_M, 1)
        cv2.line(out, (px, py - 8), (px, py + 8), C_GRAY_M, 1)
    return out


def draw_charge_arc(frame: np.ndarray, state: dict) -> np.ndarray:
    """Draw thin amber arc around palm during mode-toggle hold. Pure."""
    if state["palm_charge_start"] is None:
        return frame
    palm = state.get("palm_center")
    if palm is None:
        return frame
    out = frame.copy()
    h, w = out.shape[:2]
    cx = int(palm["x"] * w)
    cy = int(palm["y"] * h)
    elapsed = time.time() - state["palm_charge_start"]
    charge = min(1.0, elapsed / 1.0)
    end_angle = int(charge * 360)
    radius = 40
    # Arc sweeps clockwise from 12-o'clock (-90 degrees)
    cv2.ellipse(out, (cx, cy), (radius, radius), -90, 0, end_angle, C_AMBER, 1, cv2.LINE_AA)

    # Label: "PLAY IN 00.4s" or "SNAP IN 00.4s"
    target_mode = "PLAY" if state["mode"] == "snap" else "SNAP"
    remaining = max(0.0, 1.0 - elapsed)
    label = f"{target_mode} IN {remaining:04.1f}s"
    cv2.putText(out, label, (cx + radius + 6, cy + 4), FONT, FS_SM, C_AMBER, 1, cv2.LINE_AA)
    return out


def apply_shutter_flash(frame: np.ndarray, state: dict) -> np.ndarray:
    """Blend white flash over frame based on flash_frames counter. Pure."""
    ff = state["flash_frames"]
    if ff <= 0:
        return frame
    opacity = ff * 0.10
    white = np.full_like(frame, 255)
    return cv2.addWeighted(frame, 1.0 - opacity, white, opacity, 0)


# ---------------------------------------------------------------------------
# Private HUD helpers — all mutate `out` in-place, return nothing
# ---------------------------------------------------------------------------

def _draw_ruler_ticks(out: np.ndarray, h: int, w: int) -> None:
    """Tick marks along top and bottom edges."""
    major_h = 6
    minor_h = 3
    step = 80
    x = 0
    while x <= w:
        cv2.line(out, (x, 0), (x, major_h), C_BORDER_I, 1)
        cv2.line(out, (x, h - 1), (x, h - 1 - major_h), C_BORDER_I, 1)
        for sub in (16, 32, 48, 64):
            mx = x + sub
            if mx >= w:
                break
            cv2.line(out, (mx, 0), (mx, minor_h), C_BORDER_I, 1)
            cv2.line(out, (mx, h - 1), (mx, h - 1 - minor_h), C_BORDER_I, 1)
        x += step


def _draw_top_left_info(out: np.ndarray, state: dict) -> None:
    cv2.putText(out, "GCROP_v0.1", (8, 22), FONT, FS_LG, C_AMBER, 1, cv2.LINE_AA)
    cam_line = (
        f"CAM.{state['cam_index']:02d}  -  "
        f"{state['cam_width']:04d}x{state['cam_height']:04d}  -  "
        f"{state['cam_fps']:.2f}FPS"
    )
    cv2.putText(out, cam_line, (8, 38), FONT, FS_SM, C_GRAY_L, 1, cv2.LINE_AA)


def _draw_top_right_info(out: np.ndarray, state: dict, w: int) -> None:
    margin = 8

    # Line 1: HANDS 02/02
    _draw_kv_right(out, "HANDS  ", f"{state['hands_count']:02d}/02", w, margin, 22)

    # Line 2: MODE SNAP / MODE PLAY — with flash on toggle
    mode_val = state["mode"].upper()
    frames_since = state["frame_count"] - state["mode_flash_frame"]
    show_val = True
    if frames_since < 12:
        show_val = (frames_since // 3) % 2 == 0
    if show_val:
        _draw_kv_right(out, "MODE  ", mode_val, w, margin, 38)
    else:
        _draw_kv_right(out, "MODE  ", "", w, margin, 38)

    # Line 3: STATE FRAMING
    _draw_kv_right(out, "STATE  ", state["gesture"].upper(), w, margin, 54)


def _draw_kv_right(out: np.ndarray, key: str, val: str, w: int, margin: int, y: int) -> None:
    """Draw KEY VALUE right-aligned: key in gray, value in amber."""
    (kw, _), _ = cv2.getTextSize(key, FONT, FS_MED, 1)
    (vw, _), _ = cv2.getTextSize(val, FONT, FS_MED, 1)
    xv = w - margin - vw
    xk = xv - kw
    cv2.putText(out, key, (xk, y), FONT, FS_MED, C_GRAY_L, 1, cv2.LINE_AA)
    if val:
        cv2.putText(out, val, (xv, y), FONT, FS_MED, C_AMBER, 1, cv2.LINE_AA)


def _draw_bottom_left_tc(out: np.ndarray, state: dict, h: int) -> None:
    elapsed = time.time() - state["start_time"]
    fps = state["cam_fps"] or 30.0
    total_secs = int(elapsed)
    hours   = total_secs // 3600
    minutes = (total_secs % 3600) // 60
    seconds = total_secs % 60
    frames  = int((elapsed % 1.0) * fps)
    tc = f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}"

    y = h - 10
    segments = [
        ("TC  ", C_GRAY_L),
        (tc,     C_AMBER),
        ("  .  CAPS  ", C_GRAY_L),
        (f"{state['caps_count']:03d}", C_AMBER),
    ]
    x = 8
    for text, color in segments:
        cv2.putText(out, text, (x, y), FONT, FS_MED, color, 1, cv2.LINE_AA)
        (tw, _), _ = cv2.getTextSize(text, FONT, FS_MED, 1)
        x += tw


def _draw_gesture_legend(out: np.ndarray, state: dict, w: int, h: int) -> None:
    """Mode-sensitive gesture legend, bottom-right."""
    y = h - 10
    margin = 8

    if state["mode"] == "snap":
        # FRAME=CROP . 2xPINCH=CAPTURE . PALM=PLAY
        groups = [
            [("PALM", C_AMBER), ("=PLAY", C_GRAY_L)],
            [("2xPINCH", C_AMBER), ("=CAPTURE", C_GRAY_L)],
            [("FRAME", C_AMBER), ("=CROP", C_GRAY_L)],
        ]
    else:
        # PINCH=GRAB . FIST=CRUSH . PALM=SNAP
        groups = [
            [("PALM", C_AMBER), ("=SNAP", C_GRAY_L)],
            [("FIST", C_AMBER), ("=CRUSH", C_GRAY_L)],
            [("PINCH", C_AMBER), ("=GRAB", C_GRAY_L)],
        ]

    sep = "  .  "
    (sep_w, _), _ = cv2.getTextSize(sep, FONT, FS_SM, 1)

    x = w - margin
    for i, group in enumerate(groups):
        group_w = sum(cv2.getTextSize(txt, FONT, FS_SM, 1)[0][0] for txt, _ in group)
        x -= group_w
        cur_x = x
        for txt, color in group:
            cv2.putText(out, txt, (cur_x, y), FONT, FS_SM, color, 1, cv2.LINE_AA)
            (tw, _), _ = cv2.getTextSize(txt, FONT, FS_SM, 1)
            cur_x += tw
        if i < len(groups) - 1:
            x -= sep_w
            cv2.putText(out, sep, (x, y), FONT, FS_SM, C_GRAY_L, 1, cv2.LINE_AA)
