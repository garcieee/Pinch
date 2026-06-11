# Orchestrator — the only module that imports from other src modules

import sys
import os

# Allow running as `python src/main.py` from the project root
sys.path.insert(0, os.path.dirname(__file__))

import cv2
from camera import open_camera, read_frame, release_camera
from overlay import apply_base_style

WINDOW = "Pinch"


def main() -> None:
    cap = open_camera(index=0)
    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)

    try:
        while True:
            frame = read_frame(cap)
            if frame is None:
                print("Camera read failed — exiting.")
                break

            frame = apply_base_style(frame)

            cv2.imshow(WINDOW, frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break

            # Exit if the window was closed via the OS chrome
            if cv2.getWindowProperty(WINDOW, cv2.WND_PROP_VISIBLE) < 1:
                break
    finally:
        release_camera(cap)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
