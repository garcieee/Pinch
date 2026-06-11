# State shape definition and update_state(state, event) -> new_state reducer (pure)

import time

CARD_W = 180
CARD_H = 120


def make_state(cam_index: int = 0, cam_width: int = 1280, cam_height: int = 720, cam_fps: float = 30.0) -> dict:
    return {
        "start_time":      time.time(),
        "frame_count":     0,
        "cam_index":       cam_index,
        "cam_width":       cam_width,
        "cam_height":      cam_height,
        "cam_fps":         cam_fps,
        # gesture
        "gesture":         "idle",
        "hands_count":     0,
        "framing_rect":    None,    # {"x","y","w","h"} normalized 0..1
        "thumb_tips":      [],      # [{"x","y"}, ...] normalized
        "index_tips":      [],
        # stability
        "stable_frames":   0,
        "lock_threshold":  9,       # ~0.3s at 30fps
        "lock_in_secs":    None,
        "prev_rect":       None,
        # flash
        "flash_frames":    0,
        # captures
        "caps_count":      0,
        "last_snap_frame": -30,
        # function key row
        "fkey_timer":      0.0,
        # cards
        "cards":           [],
        "drag_card_id":    None,
        "drag_offset":     None,    # {"dx","dy"}
    }


def update_state(state: dict, event: dict) -> dict:
    t = event["type"]

    if t == "gesture_update":
        return {
            **state,
            "gesture":      event["gesture"],
            "hands_count":  event["hands_count"],
            "framing_rect": event["framing_rect"],
            "thumb_tips":   event["thumb_tips"],
            "index_tips":   event["index_tips"],
        }

    if t == "snap":
        caps = state["caps_count"] + 1
        label = f"CAP.{caps:03d}"
        ts = time.strftime("%H:%M:%S")
        w = event.get("frame_w", state["cam_width"])
        h = event.get("frame_h", state["cam_height"])
        rect = state["framing_rect"]
        if rect:
            sx = int(rect["x"] * w)
            sy = int(rect["y"] * h)
        else:
            sx, sy = w - CARD_W - 8, h - CARD_H - 8
        rest = _compute_single_rest(caps - 1, w, h)
        card = {
            "id":          caps,
            "label":       label,
            "timestamp":   ts,
            "image":       event["image"],
            "spawn_px":    (sx, sy),
            "pos":         (sx, sy),
            "rest_pos":    rest,
            "spawn_frame": state["frame_count"],
        }
        return {
            **state,
            "caps_count":      caps,
            "last_snap_frame": state["frame_count"],
            "flash_frames":    4,
            "gesture":         "idle",
            "cards":           state["cards"] + [card],
        }

    if t == "flash_tick":
        if state["flash_frames"] > 0:
            return {**state, "flash_frames": state["flash_frames"] - 1}
        return state

    if t == "stable_tick":
        new_rect = event.get("new_rect")
        prev_rect = state.get("prev_rect")
        if new_rect is None:
            return {**state, "stable_frames": 0, "lock_in_secs": None, "prev_rect": None}
        moved = _rect_moved(prev_rect, new_rect, threshold=0.02)
        stable = 0 if moved else state["stable_frames"] + 1
        threshold = state["lock_threshold"]
        fps = state["cam_fps"] or 30.0
        if stable < threshold:
            lock_in_secs = round((threshold - stable) / fps, 1)
        else:
            lock_in_secs = None
        return {**state, "stable_frames": stable, "lock_in_secs": lock_in_secs, "prev_rect": new_rect}

    if t == "fkey_trigger":
        return {**state, "fkey_timer": time.time()}

    if t == "card_drag_start":
        return {
            **state,
            "drag_card_id": event["id"],
            "drag_offset":  {"dx": event["dx"], "dy": event["dy"]},
        }

    if t == "card_drag_move":
        drag_id = state["drag_card_id"]
        if drag_id is None:
            return state
        off = state["drag_offset"]
        nx = event["mx"] - off["dx"]
        ny = event["my"] - off["dy"]
        cards = [
            {**c, "pos": (nx, ny)} if c["id"] == drag_id else c
            for c in state["cards"]
        ]
        return {**state, "cards": cards}

    if t == "card_drag_end":
        drag_id = state["drag_card_id"]
        cards = [
            {**c, "rest_pos": c["pos"]} if c["id"] == drag_id else c
            for c in state["cards"]
        ]
        return {**state, "drag_card_id": None, "drag_offset": None, "cards": cards}

    if t == "card_delete":
        cards = [c for c in state["cards"] if c["id"] != event["id"]]
        drag_id = state["drag_card_id"]
        return {
            **state,
            "cards":        cards,
            "drag_card_id": None if drag_id == event["id"] else drag_id,
            "drag_offset":  None if drag_id == event["id"] else state["drag_offset"],
        }

    if t == "purge_cards":
        return {**state, "cards": [], "drag_card_id": None, "drag_offset": None}

    return state


def _rect_moved(prev: dict | None, curr: dict, threshold: float) -> bool:
    if prev is None:
        return True
    return any(abs(curr.get(k, 0) - prev.get(k, 0)) > threshold for k in ("x", "y", "w", "h"))


def _compute_single_rest(index: int, frame_w: int, frame_h: int) -> tuple:
    """Cards stack from bottom-right, 2 per column (right column first)."""
    col = index // 2
    row = index % 2
    margin = 8
    x = frame_w - CARD_W - margin - col * (CARD_W + margin)
    y = frame_h - CARD_H - margin - row * (CARD_H + margin)
    return (max(0, x), max(0, y))


def compute_rest_positions(cards: list, frame_w: int, frame_h: int) -> list:
    return [_compute_single_rest(i, frame_w, frame_h) for i in range(len(cards))]
