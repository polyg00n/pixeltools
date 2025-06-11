"""
core/extractor.py

Implements AOV frame extraction from EXR sequences to standard image formats.
Optionally applies colormaps and encodes video outputs.
"""

from pathlib import Path
import imageio.v3 as iio
import numpy as np
import cv2
import OpenEXR, Imath
import os
import concurrent.futures


def extract_aovs_from_sequences(base_dir, aov_names, output_format="png", colormap=None, normalize=True, encode_video=True, parallel=True):
    """
    Extracts specified AOVs from all EXRs in a sequence directory structure.

    Parameters:
        base_dir: Path to root directory containing simulation folders.
        aov_names: List of AOV names to extract (e.g., ['depth', 'diffcol'])
        output_format: 'png' or 'jpg'
        colormap: Optional OpenCV colormap string (e.g., 'viridis')
        normalize: Whether to normalize float AOV values to [0,255]
        encode_video: Whether to write MP4s from extracted frames
        parallel: If True, extract frames concurrently
    """
    sim_dirs = [d for d in Path(base_dir).iterdir() if d.is_dir()]
    for sim_path in sim_dirs:
        frame_paths = sorted(sim_path.glob("*.exr"))
        for aov in aov_names:
            output_dir = sim_path / f"_aov_{aov}"
            output_dir.mkdir(exist_ok=True)

            def extract_and_save(frame_path):
                image = load_exr_aov(frame_path, aov)
                if image is None:
                    return
                if normalize:
                    image = normalize_float_image(image)
                if colormap:
                    cmap = getattr(cv2, f"COLORMAP_{colormap.upper()}", None)
                    if cmap:
                        image = cv2.applyColorMap(image, cmap)
                name = output_dir / f"{frame_path.stem}.{output_format}"
                cv2.imwrite(str(name), image)

            if parallel:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    executor.map(extract_and_save, frame_paths)
            else:
                for path in frame_paths:
                    extract_and_save(path)

            if encode_video:
                encode_sequence(output_dir)


def load_exr_aov(path, aov):
    """Loads a specific AOV from an EXR file and returns as grayscale uint8."""
    try:
        exr = OpenEXR.InputFile(str(path))
        dw = exr.header()['dataWindow']
        width = dw.max.x - dw.min.x + 1
        height = dw.max.y - dw.min.y + 1
        pt = Imath.PixelType(Imath.PixelType.FLOAT)

        channel_name = f"{aov}.R"
        if channel_name not in exr.header()['channels']:
            return None

        raw = exr.channel(channel_name, pt)
        data = np.frombuffer(raw, dtype=np.float32).reshape((height, width))
        return (data * 255).astype(np.uint8) if np.max(data) <= 1.0 else data.astype(np.uint8)

    except Exception as e:
        print(f"Failed to load {aov} from {path}: {e}")
        return None

def normalize_float_image(image):
    """Normalize a float32 grayscale image to 0-255 uint8 range."""
    image = image.astype(np.float32)
    if np.max(image) == 0:
        return np.zeros_like(image, dtype=np.uint8)
    image = (image - np.min(image)) / (np.max(image) - np.min(image))
    return (image * 255).astype(np.uint8)


def encode_sequence(folder):
    """Writes all frames in a folder to MP4 using OpenCV."""
    frames = sorted(folder.glob("*.png"))
    if not frames:
        return
    sample = cv2.imread(str(frames[0]))
    h, w = sample.shape[:2]
    writer = cv2.VideoWriter(str(folder / "preview.mp4"), cv2.VideoWriter_fourcc(*"mp4v"), 24, (w, h))
    for f in frames:
        img = cv2.imread(str(f))
        writer.write(img)
    writer.release()
