"""
core/thumbnail.py

Creates a summary video where each frame represents a different simulation result
at a specific frame index. Useful for qualitative comparisons.
"""

from pathlib import Path
import cv2
import numpy as np
import imageio.v3 as iio


def create_thumbnail_video(root_folder, target_frame=0, output_name="thumbnail_summary.mp4"):
    """
    Creates a summary video where each frame is a tile of the same frame number
    (e.g., frame 50) from multiple simulation sequences.

    Parameters:
        root_folder (Path or str): Directory containing multiple subfolders with sequences.
        target_frame (int): Frame index to extract (0-based).
        output_name (str): Output video filename.
    """
    root = Path(root_folder)
    sims = [d for d in root.iterdir() if d.is_dir() and not d.name.startswith("_")]
    rows = []

    for sim in sims:
        frame_paths = sorted(sim.glob("*.png")) or sorted(sim.glob("*.exr"))
        if len(frame_paths) <= target_frame:
            continue
        image = cv2.imread(str(frame_paths[target_frame]))
        if image is not None:
            rows.append(image)

    if not rows:
        print("No valid frames found to assemble thumbnail video.")
        return

    height = max(row.shape[0] for row in rows)
    width = max(row.shape[1] for row in rows)

    padded_rows = [cv2.copyMakeBorder(r, 0, height - r.shape[0], 0, width - r.shape[1], cv2.BORDER_CONSTANT) for r in rows]
    grid = np.vstack(padded_rows)

    output_path = root / output_name
    cv2.imwrite(str(output_path), grid)
    print(f"Thumbnail summary saved to {output_path}")
