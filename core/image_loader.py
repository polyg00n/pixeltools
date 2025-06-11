"""
image_loader.py

Handles reading image files (EXR, PNG, JPG), optionally with AOV selection.
Supports returning images as NumPy arrays for further processing.
"""

import cv2
import OpenEXR
import Imath
import numpy as np
from pathlib import Path


def load_image(path, aov=None):
    """
    Loads an image. If EXR and aov is specified, loads only that AOV.
    Returns a NumPy RGB image.
    """
    path = str(path)
    if path.endswith(".exr") and aov:
        exr = OpenEXR.InputFile(path)
        header = exr.header()
        dw = header["dataWindow"]
        w, h = dw.max.x - dw.min.x + 1, dw.max.y - dw.min.y + 1
        pt = Imath.PixelType(Imath.PixelType.FLOAT)

        channels = []
        for c in 'RGB':
            key = f"{aov}.{c}"
            if key in header["channels"]:
                chan = exr.channel(key, pt)
                arr = np.frombuffer(chan, dtype=np.float32).reshape(h, w)
                channels.append(arr)

        img = np.stack(channels, axis=-1)
        return (np.clip(img, 0, 1) * 255).astype(np.uint8)

    else:
        return cv2.imread(path, cv2.IMREAD_COLOR)
