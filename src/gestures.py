# Hand landmarks → gesture classification (pure)
# Uses MediaPipe Tasks API (v0.10+): result.hand_landmarks is List[List[NormalizedLandmark]]

import math


def is_index_extended(lms: list) -> bool:
    """Index fingertip (8) is above index MCP knuckle (5) — y increases downward."""
    return lms[8].y < lms[5].y


def is_pinching(lms: list) -> bool:
    """Thumb tip (4) and index tip (8) are close together."""
    dx = lms[4].x - lms[8].x
    dy = lms[4].y - lms[8].y
    return math.sqrt(dx * dx + dy * dy) < 0.06


def classify_gesture(result) -> str:
    """Return 'idle', 'framing', or 'pinch' from HandLandmarkerResult."""
    hands = result.hand_landmarks
    if not hands or len(hands) < 2:
        return "idle"
    lms0, lms1 = hands[0], hands[1]
    if is_pinching(lms0) and is_pinching(lms1):
        return "pinch"
    if (is_index_extended(lms0) and is_index_extended(lms1)
            and not is_pinching(lms0) and not is_pinching(lms1)):
        return "framing"
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


def get_hands_count(result) -> int:
    hands = result.hand_landmarks
    return len(hands) if hands else 0
