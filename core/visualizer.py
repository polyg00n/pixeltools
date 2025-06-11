"""
core/visualizer.py

Generates side-by-side or grid comparisons of AOVs from a single EXR file.
Useful for visual inspection of different render passes.
"""

import OpenEXR, Imath
import numpy as np
import cv2
from pathlib import Path

def create_aov_comparison(exr_path, aovs=None, out_name=None):
    """
    Generates a single image showing selected AOVs from one EXR file.

    Parameters:
        exr_path: Path to an EXR file
        aovs: List of AOV base names (e.g., ['diffcol', 'depth'])
        out_name: Optional name for saved PNG file
    """
    exr_path = Path(exr_path)
    if aovs is None:
        aovs = infer_aovs(exr_path)

    tiles = []
    for aov in aovs:
        tile = extract_aov_tile(exr_path, aov)
        if tile is not None:
            tiles.append(tile)

    if not tiles:
        print("No valid AOVs found to display.")
        return

    height = max(tile.shape[0] for tile in tiles)
    padded = [cv2.copyMakeBorder(img, 0, height - img.shape[0], 0, 0, cv2.BORDER_CONSTANT) for img in tiles]
    out = np.hstack(padded)

    if out_name is None:
        out_name = exr_path.with_name(exr_path.stem + "_aov_grid.png")

    cv2.imwrite(str(out_name), out)
    print(f"Saved AOV comparison to: {out_name}")


def extract_aov_tile(exr_path, aov):
    try:
        exr = OpenEXR.InputFile(str(exr_path))
        dw = exr.header()['dataWindow']
        width = dw.max.x - dw.min.x + 1
        height = dw.max.y - dw.min.y + 1
        pt = Imath.PixelType(Imath.PixelType.FLOAT)

        chan = f"{aov}.R"
        if chan not in exr.header()['channels']:
            return None

        raw = exr.channel(chan, pt)
        data = np.frombuffer(raw, dtype=np.float32).reshape((height, width))
        data = normalize_float_image(data)
        img = cv2.applyColorMap(data, cv2.COLORMAP_VIRIDIS)
        label = cv2.putText(img.copy(), aov, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 1)
        return label
    except Exception as e:
        print(f"Error extracting AOV {aov}: {e}")
        return None

def normalize_float_image(image):
    image = image.astype(np.float32)
    if np.max(image) == 0:
        return np.zeros_like(image, dtype=np.uint8)
    image = (image - np.min(image)) / (np.max(image) - np.min(image))
    return (image * 255).astype(np.uint8)

def infer_aovs(exr_path):
    """Return list of unique AOV names (without .R/.G/.B suffixes)."""
    try:
        exr = OpenEXR.InputFile(str(exr_path))
        all_channels = list(exr.header()['channels'].keys())
        return sorted(set(c.split('.')[0] for c in all_channels if '.' in c))
    except:
        return []
