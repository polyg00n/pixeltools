"""
test_comparator.py

Unit tests for comparator.py — RGB delta calculation and change flag logic.
"""

import unittest
from core import comparator

class TestComparator(unittest.TestCase):

    def test_compute_rgb_deltas(self):
        data = [[100, 100, 100], [110, 110, 110], [90, 90, 90]]
        deltas = comparator.compute_rgb_deltas(data, [100, 100, 100])
        self.assertEqual(len(deltas), 3)
        self.assertAlmostEqual(deltas[0], 0.0)

    def test_flag_changes(self):
        deltas = [0.0, 12.0, 8.0]
        flags = comparator.flag_changes(deltas, threshold=10)
        self.assertEqual(flags, [0, 1, 0])

    def test_compare_multiple_tracks(self):
        tracks = {
            "x1_y1": [[100, 100, 100], [130, 130, 130], [105, 105, 105]]
        }
        result = comparator.compare_multiple_tracks(tracks, threshold=20)
        self.assertIn("x1_y1", result)
        self.assertEqual(result["x1_y1"]["flags"], [0, 1, 0])

if __name__ == '__main__':
    unittest.main()
