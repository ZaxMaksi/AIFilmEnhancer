"""Optional image effects for a later pipeline milestone."""

import cv2
import numpy as np


def apply_contrast(image: np.ndarray, contrast: float = 1.0) -> np.ndarray:
    """Apply a restrained linear contrast adjustment."""
    return cv2.convertScaleAbs(image, alpha=contrast, beta=0)


def add_film_grain(image: np.ndarray, strength: float = 0.0) -> np.ndarray:
    """Add monochrome film grain; strength 0 leaves the image unchanged."""
    if strength <= 0:
        return image
    grain = np.random.normal(0, strength, image.shape[:2]).astype(np.int16)
    grain = np.repeat(grain[:, :, None], 3, axis=2)
    return np.clip(image.astype(np.int16) + grain, 0, 255).astype(np.uint8)


def add_bloom(image: np.ndarray, strength: float = 0.0, threshold: int = 220) -> np.ndarray:
    """Add a soft glow around the brightest image regions."""
    if strength <= 0:
        return image
    bright = cv2.threshold(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), threshold, 255, cv2.THRESH_BINARY)[1]
    glow = cv2.GaussianBlur(image, (0, 0), sigmaX=15)
    mask = cv2.GaussianBlur(bright, (0, 0), sigmaX=15)[:, :, None] / 255.0
    result = image.astype(np.float32) + glow.astype(np.float32) * mask * strength
    return np.clip(result, 0, 255).astype(np.uint8)
