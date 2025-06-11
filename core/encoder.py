from pathlib import Path
import cv2
import numpy as np
import imageio.v3 as iio

def encode_sequence(folder_path, output_name="preview.mp4", fps=24):
    """
    Encodes all .exr or .png frames in a folder into an MP4 video.
    """
    folder = Path(folder_path)
    frame_paths = sorted(folder.glob("*.exr"))
    if not frame_paths:
        frame_paths = sorted(folder.glob("*.png"))
    if not frame_paths:
        print("No frames found to encode.")
        return

    first = iio.imread(str(frame_paths[0]))
    if first.ndim == 2:
        first = np.stack([first] * 3, axis=-1)
    height, width = first.shape[:2]

    writer = cv2.VideoWriter(str(folder / output_name), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
    for f in frame_paths:
        img = iio.imread(str(f))
        if img.ndim == 2:
            img = np.stack([img] * 3, axis=-1)
        if img.dtype != np.uint8:
            img = np.clip(img, 0, 1) if img.max() <= 1.0 else img / 255.0
            img = (img * 255).astype(np.uint8)
        writer.write(img[:, :, ::-1])  # RGB to BGR for OpenCV
    writer.release()
    print(f"Video saved to: {folder / output_name}")
