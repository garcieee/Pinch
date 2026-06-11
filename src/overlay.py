# Draw crop rectangle, landmarks, and shutter flash onto frame (pure)

import cv2
import numpy as np


def apply_base_style(frame: np.ndarray) -> np.ndarray:
    """Apply subtle dark vignette + 1px border. Pure — returns a new frame."""
    h, w = frame.shape[:2]
    cx, cy = w / 2.0, h / 2.0

    # Gaussian vignette: bright at center, dims toward edges
    Y, X = np.ogrid[:h, :w]
    sigma_x = w * 0.65
    sigma_y = h * 0.65
    gauss = (
        np.exp(-((X - cx) ** 2) / (2 * sigma_x ** 2))
        * np.exp(-((Y - cy) ** 2) / (2 * sigma_y ** 2))
    )
    # Remap so center stays at 1.0 and corners fall to ~0.55
    vignette = 0.55 + 0.45 * (gauss / gauss.max())
    vignette = vignette[:, :, np.newaxis]  # broadcast over RGB channels

    styled = np.clip(frame * vignette, 0, 255).astype(np.uint8)

    # 1px border — set edge rows/cols to near-black
    styled[0, :] = 20
    styled[-1, :] = 20
    styled[:, 0] = 20
    styled[:, -1] = 20

    return styled
