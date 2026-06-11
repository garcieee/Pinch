# Webcam capture and frame loop

import cv2
import numpy as np


def open_camera(index: int = 0) -> cv2.VideoCapture:
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open camera at index {index}. "
                           "Check that a webcam is connected and not in use.")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    return cap


def read_frame(cap: cv2.VideoCapture) -> np.ndarray | None:
    ok, frame = cap.read()
    if not ok:
        return None
    return cv2.flip(frame, 1)  # horizontal flip — mirror/selfie mode


def release_camera(cap: cv2.VideoCapture) -> None:
    cap.release()
