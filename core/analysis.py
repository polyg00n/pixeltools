"""
core/analysis.py

Provides utilities to analyze the structure and consistency of simulation datasets.
Useful for quality checks and feature discovery.
"""

from pathlib import Path
from collections import defaultdict
import OpenEXR


def analyze_dataset(root_dir):
    """
    Scans the given directory for simulation subfolders and image sequence files.
    Returns statistics about:
    - number of sequences
    - frame counts per sequence
    - unique AOVs across EXR files
    - resolution variance
    """
    stats = {
        "sequence_count": 0,
        "frame_counts": {},
        "unique_aovs": set(),
        "resolutions": set(),
    }

    root = Path(root_dir)
    sim_dirs = [d for d in root.iterdir() if d.is_dir()]
    stats["sequence_count"] = len(sim_dirs)

    for sim in sim_dirs:
        exrs = sorted(sim.glob("*.exr"))
        stats["frame_counts"][sim.name] = len(exrs)
        for exr_file in exrs[:1]:  # Only sample the first file
            try:
                with OpenEXR.InputFile(str(exr_file)) as f:
                    header = f.header()
                    aovs = [c.split('.')[0] for c in header['channels'].keys() if '.' in c]
                    stats["unique_aovs"].update(aovs)
                    dw = header["dataWindow"]
                    w, h = dw.max.x - dw.min.x + 1, dw.max.y - dw.min.y + 1
                    stats["resolutions"].add((w, h))
            except Exception as e:
                print(f"Error reading {exr_file}: {e}")

    return stats


def print_dataset_stats(stats):
    """
    Pretty-prints the dictionary returned by analyze_dataset().
    """
    print("\n--- Dataset Summary ---")
    print(f"Sequences found: {stats['sequence_count']}")
    print("Frame counts:")
    for name, count in stats["frame_counts"].items():
        print(f"  {name}: {count} frames")
    print(f"Unique AOVs detected: {sorted(stats['unique_aovs'])}")
    print(f"Resolutions: {stats['resolutions']}")
