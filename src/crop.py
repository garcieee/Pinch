# Frame + bounding box → cropped image (pure)

import os
import cv2
import numpy as np


def norm_rect_to_px(rect_norm: dict, w: int, h: int) -> tuple:
    """Convert normalized rect to pixel coords, clamped to frame bounds."""
    x1 = max(0, int(rect_norm["x"] * w))
    y1 = max(0, int(rect_norm["y"] * h))
    x2 = min(w, int((rect_norm["x"] + rect_norm["w"]) * w))
    y2 = min(h, int((rect_norm["y"] + rect_norm["h"]) * h))
    return x1, y1, x2, y2


def extract_crop(frame: np.ndarray, rect_norm: dict) -> np.ndarray:
    """Return a copy of the region defined by rect_norm from frame."""
    h, w = frame.shape[:2]
    x1, y1, x2, y2 = norm_rect_to_px(rect_norm, w, h)
    if x2 <= x1 or y2 <= y1:
        return np.zeros((1, 1, 3), dtype=np.uint8)
    return frame[y1:y2, x1:x2].copy()


def save_crop(image: np.ndarray, index: int,
              directory: str = "/tmp/pinch_caps") -> str:
    """Write cropped image to disk. Returns the file path."""
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, f"CAP_{index:03d}.png")
    cv2.imwrite(path, image)
    return path
