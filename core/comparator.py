"""
comparator.py

Contains utilities for measuring pixel-level color differences and
classifying whether a change occurred using thresholds.
"""

import numpy as np

def compute_rgb_deltas(rgb_sequence, base_rgb=None):
    """
    Computes per-frame Euclidean distance to base RGB.
    """
    base = np.array(base_rgb or rgb_sequence[0])
    return [np.linalg.norm(np.array(rgb) - base) for rgb in rgb_sequence]

def flag_changes(deltas, threshold=10):
    """
    Converts distance values into binary flags using a threshold.
    """
    return [int(d > threshold) for d in deltas]

def compare_multiple_tracks(track_data, threshold=10):
    """
    Given a dictionary of pixel_id -> [rgb_sequence], return delta + flags.
    """
    results = {}
    for key, sequence in track_data.items():
        deltas = compute_rgb_deltas(sequence)
        flags = flag_changes(deltas, threshold)
        results[key] = {
            "deltas": deltas,
            "flags": flags,
            "rgb": sequence
        }
    return results
