# Hand landmarks → gesture classification (pure)
# Uses MediaPipe Tasks API (v0.10+): result.hand_landmarks is List[List[NormalizedLandmark]]

import math


def is_index_extended(lms: list) -> bool:
    """Index fingertip (8) is above index MCP knuckle (5) — y increases downward."""
    return lms[8].y < lms[5].y


def is_thumb_extended(lms: list) -> bool:
    """Thumb tip (4) is further from wrist (0) than thumb IP joint (3)."""
    dx_tip = lms[4].x - lms[0].x
    dy_tip = lms[4].y - lms[0].y
    dx_ip = lms[3].x - lms[0].x
    dy_ip = lms[3].y - lms[0].y
    return (dx_tip * dx_tip + dy_tip * dy_tip) > (dx_ip * dx_ip + dy_ip * dy_ip)


def _is_finger_extended(lms: list, tip: int, pip: int) -> bool:
    """Generic: fingertip is above its PIP joint (y decreases upward)."""
    return lms[tip].y < lms[pip].y


def is_open_palm(lms: list) -> bool:
    """All 5 fingers extended."""
    return (is_thumb_extended(lms)
            and _is_finger_extended(lms, 8, 6)     # index
            and _is_finger_extended(lms, 12, 10)    # middle
            and _is_finger_extended(lms, 16, 14)    # ring
            and _is_finger_extended(lms, 20, 18))   # pinky


def is_pinching(lms: list) -> bool:
    """Thumb tip (4) and index tip (8) are close together."""
    dx = lms[4].x - lms[8].x
    dy = lms[4].y - lms[8].y
    return math.sqrt(dx * dx + dy * dy) < 0.06


def _is_framing_hand(lms: list) -> bool:
    """Thumb + index extended, middle NOT extended, not pinching — deliberate frame."""
    return (is_thumb_extended(lms)
            and is_index_extended(lms)
            and not _is_finger_extended(lms, 12, 10)
            and not is_pinching(lms))


def classify_gesture(result) -> str:
    """Return gesture string from HandLandmarkerResult.

    Returns: 'idle', 'framing', 'pinch', 'palm', 'single_pinch'
    """
    hands = result.hand_landmarks
    if not hands:
        return "idle"

    # --- single hand ---
    if len(hands) == 1:
        lms = hands[0]
        if is_open_palm(lms):
            return "palm"
        if is_pinching(lms):
            return "single_pinch"
        return "idle"

    # --- two hands ---
    lms0, lms1 = hands[0], hands[1]

    if is_pinching(lms0) and is_pinching(lms1):
        return "pinch"

    if _is_framing_hand(lms0) and _is_framing_hand(lms1):
        return "framing"

    if is_open_palm(lms0) or is_open_palm(lms1):
        return "palm"

    if is_pinching(lms0) or is_pinching(lms1):
        return "single_pinch"

    return "idle"


def get_framing_rect(result) -> dict | None:
    """Bounding box of all 4 fingertips (thumb + index from each hand), normalized."""
    hands = result.hand_landmarks
    if not hands or len(hands) < 2:
        return None
    pts_x, pts_y = [], []
    for lms in hands:
        for idx in (4, 8):  # thumb tip, index tip
            pts_x.append(lms[idx].x)
            pts_y.append(lms[idx].y)
    x = min(pts_x)
    y = min(pts_y)
    w = max(pts_x) - x
    h = max(pts_y) - y
    return {"x": x, "y": y, "w": w, "h": h}


def get_fingertip_positions(result) -> tuple:
    """Return (thumb_tips, index_tips) — each a list of {"x","y"} dicts, normalized."""
    hands = result.hand_landmarks
    if not hands:
        return [], []
    thumb_tips, index_tips = [], []
    for lms in hands:
        thumb_tips.append({"x": lms[4].x, "y": lms[4].y})
        index_tips.append({"x": lms[8].x, "y": lms[8].y})
    return thumb_tips, index_tips


def get_pinch_midpoint(result) -> dict | None:
    """Return normalized {x,y} midpoint of the first pinching hand, or None."""
    hands = result.hand_landmarks
    if not hands:
        return None
    for lms in hands:
        if is_pinching(lms):
            return {"x": (lms[4].x + lms[8].x) / 2,
                    "y": (lms[4].y + lms[8].y) / 2}
    return None


def get_palm_center(result) -> dict | None:
    """Return normalized {x,y} center of the first open-palm hand, or None."""
    hands = result.hand_landmarks
    if not hands:
        return None
    for lms in hands:
        if is_open_palm(lms):
            return {"x": (lms[0].x + lms[9].x) / 2,
                    "y": (lms[0].y + lms[9].y) / 2}
    return None


def get_hands_count(result) -> int:
    hands = result.hand_landmarks
    return len(hands) if hands else 0
