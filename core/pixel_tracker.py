"""
pixel_tracker.py

Provides functions for tracking RGB values of specified pixel coordinates
across sequences of image frames.
"""

import numpy as np

class PixelTracker:
    def __init__(self, coordinates=None):
        """
        coordinates: list of (x, y) tuples to track
        """
        self.coordinates = coordinates or []
        self.data = {}  # Maps coordinate key -> list of RGB values per frame

    def add_pixel(self, x, y):
        key = f"x{x}_y{y}"
        if key not in self.data:
            self.data[key] = []
            self.coordinates.append((x, y))

    def track_frame(self, frame):
        """
        frame: numpy array image (H x W x 3)
        """
        for (x, y) in self.coordinates:
            rgb = frame[y, x].tolist()
            self.data[f"x{x}_y{y}"].append(rgb)

    def get_data(self):
        return self.data

    def compute_change_flags(self, tolerance=10):
        """
        Returns binary flags per pixel per frame, indicating whether the
        RGB value changed more than the given tolerance (Euclidean distance).
        """
        flags = {}
        for key, values in self.data.items():
            base = np.array(values[0])
            flags[key] = [(np.linalg.norm(np.array(v) - base) > tolerance) for v in values]
        return flags
