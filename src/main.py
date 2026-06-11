# Orchestrator — the only module that imports from other src modules

import sys
import os

# Allow running as `python src/main.py` from the project root
sys.path.insert(0, os.path.dirname(__file__))

import cv2
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions, RunningMode

from camera import open_camera, read_frame, release_camera
from state import make_state, update_state
from gestures import classify_gesture, get_framing_rect, get_fingertip_positions, get_hands_count
from overlay import apply_base_style, draw_crop_rect, draw_fingertip_markers, apply_shutter_flash
from cards import render_cards, hit_test_delete_btn, hit_test_card_body, get_card_pos
from crop import extract_crop

WINDOW = "Pinch"


def main() -> None:
    cap = open_camera(index=0)
    cam_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    cam_w   = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    cam_h   = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    state = make_state(cam_index=0, cam_width=cam_w, cam_height=cam_h, cam_fps=cam_fps)

    model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "hand_landmarker.task")
    mp_options = HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=model_path),
        running_mode=RunningMode.IMAGE,
        num_hands=2,
        min_hand_detection_confidence=0.7,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    mp_hands = HandLandmarker.create_from_options(mp_options)

    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)

    def on_mouse(event, mx, my, flags, param):
        nonlocal state
        fc = state["frame_count"]
        if event == cv2.EVENT_LBUTTONDOWN:
            # Hit-test top card first (last in list = drawn on top)
            for card in reversed(state["cards"]):
                pos = get_card_pos(card, fc)
                if hit_test_delete_btn(card, pos, mx, my):
                    state = update_state(state, {"type": "card_delete", "id": card["id"]})
                    return
                if hit_test_card_body(card, pos, mx, my):
                    dx = mx - pos[0]
                    dy = my - pos[1]
                    # Sync pos to current animated position before dragging
                    cards = [
                        {**c, "pos": pos, "rest_pos": pos} if c["id"] == card["id"] else c
                        for c in state["cards"]
                    ]
                    state = {**state, "cards": cards}
                    state = update_state(state, {"type": "card_drag_start", "id": card["id"], "dx": dx, "dy": dy})
                    return
        elif event == cv2.EVENT_MOUSEMOVE:
            if state["drag_card_id"] is not None:
                state = update_state(state, {"type": "card_drag_move", "mx": mx, "my": my})
        elif event == cv2.EVENT_LBUTTONUP:
            if state["drag_card_id"] is not None:
                state = update_state(state, {"type": "card_drag_end"})

    cv2.setMouseCallback(WINDOW, on_mouse)

    try:
        while True:
            frame = read_frame(cap)
            if frame is None:
                print("Camera read failed — exiting.")
                break

            h, w = frame.shape[:2]

            # --- MediaPipe hand detection ---
            rgb        = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image   = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            results    = mp_hands.detect(mp_image)

            new_gesture    = classify_gesture(results)
            new_rect       = get_framing_rect(results)
            thumb_t, idx_t = get_fingertip_positions(results)
            hands_n        = get_hands_count(results)

            # --- State updates ---
            state = update_state(state, {
                "type":         "gesture_update",
                "gesture":      new_gesture,
                "hands_count":  hands_n,
                "framing_rect": new_rect,
                "thumb_tips":   thumb_t,
                "index_tips":   idx_t,
            })

            # Snap on pinch (with debounce)
            if (new_gesture == "pinch"
                    and state["framing_rect"] is not None
                    and state["frame_count"] - state["last_snap_frame"] > 20):
                crop_img = extract_crop(frame, state["framing_rect"])
                state = update_state(state, {
                    "type":    "snap",
                    "image":   crop_img,
                    "frame_w": w,
                    "frame_h": h,
                })

            state = update_state(state, {"type": "flash_tick"})
            state = update_state(state, {"type": "stable_tick", "new_rect": new_rect})

            if hands_n > 0:
                state = update_state(state, {"type": "fkey_trigger"})

            state = {**state, "frame_count": state["frame_count"] + 1}

            # --- Draw ---
            frame = apply_base_style(frame, state)
            frame = draw_crop_rect(frame, state)
            frame = draw_fingertip_markers(frame, state)
            frame = render_cards(frame, state)
            frame = apply_shutter_flash(frame, state)

            cv2.imshow(WINDOW, frame)

            # --- Input ---
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key in (ord("1"), ord("2"), ord("3"), ord("x"), ord("X")):
                state = update_state(state, {"type": "fkey_trigger"})
            if key in (ord("x"), ord("X")):
                state = update_state(state, {"type": "purge_cards"})

            if cv2.getWindowProperty(WINDOW, cv2.WND_PROP_VISIBLE) < 1:
                break
    finally:
        mp_hands.close()  # type: ignore[attr-defined]
        release_camera(cap)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
